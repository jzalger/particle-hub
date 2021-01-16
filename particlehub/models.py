import time
import pickle
import requests
import multiprocessing
import simplejson as json
from string import Template
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError

BASE_PARTICLE_URL = "https://api.particle.io/v1/"


###################################################################################################
# General API Classes

class ParticleCloud:

    def __init__(self, cloud_api_token):
        self.cloud_api_token = cloud_api_token

    def get_devices(self):
        url = BASE_PARTICLE_URL + "devices"
        request = requests.get(url, params=dict(access_token=self.cloud_api_token))
        if request.status_code == requests.codes.ok:
            devices = dict()
            device_list = request.json()
            for device_dict in device_list:
                device = Device.from_dict(device_dict, self.cloud_api_token)
                devices[device.id] = device
            return devices
        else:
            raise CloudCommunicationError


class HubManager:

    def __init__(self, cloud_api_token, devices=None, log_managers=None, state_filename="particle_hub.state"):
        self.cloud = ParticleCloud(cloud_api_token)
        self.devices = devices
        self.state_filename = state_filename
        self.log_managers = log_managers

        self.update_device_list()

        if log_managers is None:
            self.log_managers = dict()

    @classmethod
    def from_state_file(cls, cloud_api_token, state_filename="particle_hub.state"):
        state = HubManager._return_state(state_filename)
        if state is None:
            raise StateNotFoundError
        else:
            return cls(cloud_api_token, devices=state["devices"],
                       log_managers=state["log_managers"], state_filename=state_filename)

    def update_device_list(self):
        try:
            new_devices = self.cloud.get_devices()
            if self.devices is not None:
                for device in self.devices:
                    if device in new_devices:
                        new_devices[device].tags = self.devices[device].tags
            self.devices = new_devices
            self.save_state()
        except CloudCommunicationError:
            self.devices = None

    def add_log_manager(self, device, log_source, log_credentials):
        device.log_managed = True
        manager = LogManager(device, log_source=log_source, log_credentials=log_credentials)
        self.log_managers[device.id] = manager
        self.save_state()

    def remove_log_manager(self, device_id):
        log_manager = self.log_managers[device_id]
        device = self.devices[device_id]
        device.log_managed = False
        log_manager.stop_logging()  # Call stop here to make sure threads are killed.
        del self.log_managers[device_id]
        self.save_state()

    @staticmethod
    def _return_state(state_filename):
        """Load the previous program state from a pickle file"""
        try:
            with open(state_filename, "rb") as state_file:
                state = pickle.load(state_file)
            return state
        except FileNotFoundError:
            return None

    def save_state(self):
        """Save the current app state to disk as a pickle file."""
        state = dict(devices=self.devices, log_managers=self.log_managers)
        with open(self.state_filename, "wb") as state_file:
            pickle.dump(state, state_file)


class LogManager:

    def __init__(self, device, log_source="influx", log_credentials=None, log_interval=300):
        self.device = device
        self.log_source = log_source
        self.log_credentials = log_credentials
        self.is_logging = False
        self.log_interval = log_interval
        self.log_function = log_functions[log_source]
        self.process = None

    def start_logging(self):
        self.is_logging = True
        self.device.is_logging = True
        self.process = multiprocessing.Process(target=self.log_loop)
        self.process.start()

    def stop_logging(self):
        self.is_logging = False
        self.device.is_logging = False
        try:
            self.process.log = False
            self.process.terminate()
            self.process.join()
        except AttributeError:
            pass

    def log_loop(self):
        process = multiprocessing.current_process()
        while getattr(process, "log", True):
            self.device.get_all_variable_data()
            self.log_function(data=self.device.variable_state,
                              log_credentials=self.log_credentials,
                              tags=self.device.tags)
            time.sleep(self.log_interval)


###################################################################################################
# Log Functions

def _log_to_influx(data, log_credentials=None, tags=None):
    for variable_name, value in data.items():
        if variable_name in tags:
            break
        point = [{"measurement": variable_name, "fields": {"value": value}, "tags": tags}]
        try:
            client = InfluxDBClient(**log_credentials)
            client.write_points(point)
        except InfluxDBClientError:
            print("InfluxDBClientError")
        except InfluxDBServerError:
            print("InfluxDBServerError")


log_functions = dict(influx=_log_to_influx)


###################################################################################################
# Device Classes

class Device:
    DEVICE_TYPE = "unknown"
    API_DEVICE_URL = Template(BASE_PARTICLE_URL + "devices/$id/")
    API_GET_URL = Template(BASE_PARTICLE_URL + "devices/$id/$var_name")
    API_FUNC_URL = Template(BASE_PARTICLE_URL + "devices/$id/$func_name")
    API_VITALS_URL = Template(BASE_PARTICLE_URL + "diagnostics/$id/last")

    def __init__(self, device_id, cloud_api_token, name=None, tags=None, variables=None, variable_state=None,
                 notes=None, connected=None, online=None, status=None, log_managed=False):
        self.id = device_id
        self.log_managed = log_managed
        self.cloud_api_token = cloud_api_token
        self.name = name
        self.tags = tags
        self.variables = variables
        self.variable_state = variable_state
        self.notes = notes
        self.connected = connected
        self.online = online
        self.status = status
        self.is_logging = False

        if variable_state is None:
            self.variable_state = dict()
        if tags is None:
            self.tags = dict()

    def __str__(self):
        return f'Device id: {self.id}\nname: {self.name}\nvariables: {self.variables}'

    @classmethod
    def from_dict(cls, input_dict, cloud_api_token):
        return cls(input_dict["id"], cloud_api_token, name=input_dict["name"], variables=input_dict["variables"],
                   notes=input_dict["notes"], connected=input_dict["connected"], online=input_dict["online"],
                   status=input_dict["status"])

    def get_all_variable_data(self):
        if self.tags is not None:
            for tag in self.tags:
                tag_val = self.get_variable_data(tag)
                self.tags[tag] = tag_val

        for variable in self.variables:
            try:
                self.variable_state[variable] = self.get_variable_data(variable)
            except requests.exceptions.RequestException:
                pass

    def device_health(self):
        raise NotImplementedError

    def _update_variable_names(self):
        """Queries the variables available with this device"""
        new_info = self.full_device_data()
        self.variables = json.loads(new_info)["variables"]

    def full_device_data(self):
        new_info = send_get_request(url=Device.API_DEVICE_URL.substitute(dict(id=self.id)),
                                    params=dict(access_token=self.cloud_api_token))
        new_info["tags"] = self.tags
        return new_info

    def get_variable_data(self, var):
        """Returns the current device state as a JSON formatted string"""
        if var not in self.variables:
            return dict()
        val = send_get_request(url=Device.API_GET_URL.substitute(dict(id=self.id, var_name=var)),
                               params=dict(access_token=self.cloud_api_token))
        return val["result"]

    def _call_func(self, func_name, arg):
        result = send_post_request(url=Device.API_FUNC_URL.substitute(
            dict(id=self.id, func_name=func_name)),
            data=dict(args=str(arg), access_token=self.cloud_api_token),
            except_return=False)
        return result


###################################################################################################
# General Methods

def send_get_request(url, params, except_return=None):
    try:
        r = requests.get(url, params=params)
        if r.status_code == requests.codes.ok:
            return dict(r.json())
        else:
            return None
    except requests.exceptions.RequestException:
        return except_return


def send_post_request(url, data, except_return=False):
    try:
        r = requests.post(url, data=data)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return except_return


###################################################################################################
# Exceptions
class StateNotFoundError(Exception):
    pass


class LogStartError(Exception):
    pass


class LogStopError(Exception):
    pass


class CloudCommunicationError(Exception):
    pass

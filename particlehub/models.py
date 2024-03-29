import pickle
import os
import logging
import requests
import sseclient
import threading
import simplejson as json
from string import Template
from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError, InfluxDBServerError

BASE_PARTICLE_URL = "https://api.particle.io/v1/"
phlog = logging.getLogger("particle-hub.models")


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
            if phlog:
                phlog.error("Cloud Communication error in get_devices")
                phlog.debug(request)
            raise CloudCommunicationError


class HubManager:

    def __init__(self, cloud_api, stream_config, event_callbacks, log_dest, log_credentials, devices=None,
                 managed_devices=None):
        self.event_callbacks = event_callbacks
        self.cloud = cloud_api
        self.devices = devices
        self.managed_devices = managed_devices
        if managed_devices is None:
            self.managed_devices = dict()
        self.update_device_list()
        self.load_state()
        self.stream_manager = StreamManager(stream_config, event_callbacks, log_dest, log_credentials,
                                            managed_devices=self.managed_devices)
        self.stream_manager.start_stream()

    def update_device_list(self):
        # This needs to be more sophistocated to not overwrite existing device objects that may be modified.
        # Need to add devices that dont exist, and update meta data for existing objects
        try:
            new_devices = self.cloud.get_devices()
            if self.devices is not None:
                for device_id in self.devices:
                    if device_id in new_devices:
                        new_devices[device_id].tags = self.devices[device_id].tags
                        new_devices[device_id].is_managed = self.devices[device_id].is_managed
            self.devices = new_devices
        except CloudCommunicationError:
            self.devices = None

    def update_device_data(self, device_id):
        """
            Enables manual device update from UI
        """
        device = self.devices[device_id]
        device.get_all_variable_data()
        for callback in self.event_callbacks:
            callback(device.variable_state)

    def add_device(self, device_id):
        device = self.devices[device_id]
        device.is_managed = True
        self.managed_devices[device_id] = device
        self.stream_manager.managed_devices = self.managed_devices
        self.save_state()

    def remove_device(self, device_id):
        device = self.devices[device_id]
        device.is_managed = False
        del self.managed_devices[device_id]
        self.stream_manager.managed_devices = self.managed_devices
        self.save_state()

    def add_tag(self, device_id, tag):
        device = self.devices[device_id]
        try:
            if device.online:
                device.tags[tag] = device.get_variable_data(tag)
                self.save_state()
                return True
        except (KeyError, AttributeError):
            return False

    def remove_tag(self, device_id, tag):
        try:
            device = self.devices[device_id]
            device.tags.pop(tag)
            self.save_state()
            return True
        except (KeyError, AttributeError):
            return False

    def save_state(self):
        """
        Gathers data requiring persistence and passes to internal state_save method

        :return: (None)
        """
        if self.devices is not None:
            state_data = dict(managed_device_ids=list(self.managed_devices.keys()),
                              tags={device_id: device.tags for device_id, device in self.devices.items()})
            self._save_state(state_data)

    @staticmethod
    def _save_state(data):
        """
        Executes the specific persistence method with aggregated data

        :param data: (dict)

        :return: (None)
        """
        state_filename = os.environ['PHSTATE_FILE']
        with open(state_filename, 'wb') as state_file:
            pickle.dump(data, state_file)

    def load_state(self):
        """
        Retrieves state data from persistence method and populates the instance.

        :return: (None)
        """
        state_data = self._load_state()
        if state_data is not None:
            self.managed_devices = {device_id: device for device_id, device in self.devices.items() if device_id in state_data['managed_device_ids']}
            for device_id, device in self.managed_devices.items():
                device.is_managed = True
            for device_id, tags in state_data['tags'].items():
                self.devices[device_id].tags = tags

    @staticmethod
    def _load_state():
        """
        Executes the specific persistence retrieval method.

        :return: (dict)
        """
        state_filename = os.environ['PHSTATE_FILE']
        if os.path.exists(state_filename):
            with open(state_filename, 'rb') as state_file:
                return pickle.load(state_file)
        else:
            return None


class StreamManager(object):

    def __init__(self, stream_config, callbacks, log_dest=None, log_credentials=None, managed_devices=None,
                 subscribed_events=None):
        """
            stream_config (dict):      url, headers
            log_dest (str):            string defining the log database to use
            log_credentials (dict):    DB credentials
            callbacks (list):          [func1, func2]
            managed_devices (dict):    List of device objects to log [id1:device1, id2:device2]
            subscribed_events (list):  List of Particle Publish event names to respond to 
        """
        self.stream_config = stream_config
        self.callbacks = callbacks
        self.managed_devices = managed_devices
        self.log_credentials = log_credentials
        self.event_handlers = dict(LOG=self._handle_log, ERROR=self._handle_error, DATA=self._handle_data)
        if subscribed_events is None:
            self.subscribed_events = ["LOG", "DATA", "ERROR"]
        if log_dest is not None:
            self.log_function = log_functions[log_dest]
            self.db_logging = True
        else:
            self.log_function = None
            self.db_logging = False

        self.stream_thread = threading.Thread(target=self._start_stream, name="PHStreamThread")

    def start_stream(self):
        self.stream_thread.start()

    def stop_stream(self):
        self.stream_thread.join(timeout=1)

    def _start_stream(self):
        stream = sseclient.SSEClient(self.stream_config["url"])
        for event in stream:
            if event.data != "":
                self._handle_msg(event)

    def _handle_msg(self, event):
        event_data = dict(json.loads(event.data))  # Parses the top level Particle.IO structure
        event_name = event.event
        if event_data['coreid'] in self.managed_devices.keys() and event_name in self.subscribed_events:
            device = self.managed_devices[event_data['coreid']]
            handler = self.event_handlers[event_name]
            handler(event_data, device)
            for callback in self.callbacks:  # Other system callbacks
                callback(event)

    def _handle_data(self, data, device):
        """
        data (dict)        full event data dict
        device (Device)    device object

        ParticleHub Schema: "key1=val1,key2=val2"
        """
        device_data_pairs = data['data'].split(",")
        device_data_pairs = [pair.split("=") for pair in device_data_pairs]
        device_data = {pair[0]: pair[1] for pair in device_data_pairs}
        device_data['timestamp'] = data['published_at']

        if self.db_logging:
            self.log_function(device_data, self.log_credentials, device.tags)

    def _handle_log(self, data, device):
        """
        data (dict)
        device (Device)
        """
        if self.db_logging:
            self.log_function({"LOG": data['data']}, self.log_credentials, device.tags)

    def _handle_error(self, data, device):
        """
        data (dict)
        device (Device)
        """
        if self.db_logging:
            self.log_function({"ERROR": data['data']}, self.log_credentials, device.tags)


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
        except InfluxDBClientError as e:
            phlog.error("InfluxDBClientError")
            phlog.debug(e)
        except InfluxDBServerError as e:
            phlog.error("InfluxDBServerError")
            phlog.debug(e)


log_functions = dict(influx=_log_to_influx)
log_query_functions = dict(influx=None)


###################################################################################################
# Device Classes

class Device:
    DEVICE_TYPE = "unknown"
    API_DEVICE_URL = Template(BASE_PARTICLE_URL + "devices/$id/")
    API_GET_URL = Template(BASE_PARTICLE_URL + "devices/$id/$var_name")
    API_FUNC_URL = Template(BASE_PARTICLE_URL + "devices/$id/$func_name")
    API_VITALS_URL = Template(BASE_PARTICLE_URL + "diagnostics/$id/last")

    def __init__(self, device_id, cloud_api_token, name=None, tags=None, variables=None, variable_state=None,
                 notes=None, connected=None, online=None, status=None, is_managed=False):
        self.id = device_id
        self.cloud_api_token = cloud_api_token
        self.name = name
        self.tags = tags
        self.variables = variables
        self.variable_state = variable_state
        self.notes = notes
        self.connected = connected
        self.online = online
        self.status = status
        self.is_managed = is_managed

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
        if val is not None:
            return val["result"]
        else:
            phlog.warning("get_variable_data returned None or failed")
            phlog.debug(val)
            return None

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
        phlog.error("send_get_request RequestException")
        phlog.debug(url)
        phlog.debug(params)
        return except_return


def send_post_request(url, data, except_return=False):
    try:
        r = requests.post(url, data=data)
        if r.status_code == requests.codes.ok:
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        phlog.error("send_post_request RequestException")
        phlog.debug(url)
        phlog.debug(data)
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

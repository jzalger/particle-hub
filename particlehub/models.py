import requests
import simplejson as json
from string import Template
from influxdb import InfluxDBClient

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
            devices = request.json()
            return devices
        else:
            return None


class HubManager:

    def __init__(self, cloud_api_token):
        self.cloud = ParticleCloud(cloud_api_token)
        self.devices = None
        self.log_managers = None
        self.threadpool = None

        self.update_device_list()

    def update_device_list(self):
        try:
            self.devices = self.cloud.get_devices()
        except:
            return None

    def add_log_manager(self, device, log_source, log_credentials):
        device.log_managed = True
        manager = LogManager(device, log_source=log_source, log_credentials=log_credentials)
        self.log_managers[device.device_id] = manager


class LogManager:

    def __init__(self, device, log_source="influx", log_credentials=None):
        self.device = device
        self.log_source = log_source
        self.log_credentials = log_credentials

    def _log_to_influx(self, new_data, tags=None):
        point = [{"measurement": new_data["name"], "fields": {"value": new_data["result"]}}]
        if tags is not None:
            point[0]["tags"] = tags
        try:
            # InfluxDBClient(influx_host, influx_port, influx_user, influx_password, influx_db_name)
            client = InfluxDBClient(**self.log_credentials)
            client.write_points(point)
        except:
            pass


###################################################################################################
# Device Classes

class Device:
    DEVICE_TYPE = "unknown"
    API_DEVICE_URL = Template(BASE_PARTICLE_URL + "devices/$device_id/")
    API_GET_URL = Template(BASE_PARTICLE_URL + "devices/$device_id/$var_name")
    API_FUNC_URL = Template(BASE_PARTICLE_URL + "devices/$device_id/$func_name")
    API_VITALS_URL = Template(BASE_PARTICLE_URL + "diagnostics/$device_id/last")

    def __init__(self, device_id, cloud_api_token, name=None, tags=None, variables=None, variable_state=None,
                 notes=None, connected=None, online=None, status=None, log_managed=False):
        self.device_id = device_id
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

    @classmethod
    def from_dict(cls, input_dict, cloud_api_token):
        return cls(input_dict["id"], cloud_api_token, name=input_dict["name"], variables=input_dict["variables"],
                   notes=input_dict["notes"], connected=input_dict["connected"], online=input_dict["online"],
                   status=input_dict["status"])

    def get_all_variable_data(self):
        for tag in self.tags:
            tag_val = self.get_variable_data(tag)
            self.tags[tag] = tag_val["result"]

        for variable in self.variables:
            try:
                self.variable_state[variable] = self.get_variable_data(variable)
            except requests.exceptions.RequestException:
                # TODO: Log this failure somewhere
                pass

    def device_health(self):
        raise NotImplementedError

    def _update_variable_names(self):
        """Queries the variables available with this device"""
        new_info = self.full_device_data()
        self.variables = json.loads(new_info)["variables"]

    def full_device_data(self):
        new_info = send_get_request(url=Device.API_DEVICE_URL.substitute(dict(device_id=self.device_id)),
                                    params=dict(access_token=self.cloud_api_token))
        return json.loads(new_info)

    def get_variable_data(self, var):
        """Returns the current device state as a JSON formatted string"""
        if var not in self.variables:
            return dict()
        val = send_get_request(url=Device.API_GET_URL.substitute(dict(device_id=self.device_id, var_name=var)),
                               params=dict(access_token=self.cloud_api_token))
        return val

    def _call_func(self, func_name, arg):
        result = send_post_request(url=Device.API_FUNC_URL.substitute(
            dict(device_id=self.device_id, func_name=func_name)),
            data=dict(args=str(arg), access_token=self.cloud_api_token),
            except_return=False)
        return result


###################################################################################################
# General Methods

def send_get_request(url, params, except_return=None):
    try:
        r = requests.get(url, params=params)
        if r.status_code == requests.codes.ok:
            return dict(r.json())["result"]
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

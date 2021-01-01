import requests
from string import Template

BASE_URL = "https://api.particle.io/v1/"


###################################################################################################
# General API Classes

class ParticleCloud:

    def __init__(self, cloud_api_token):
        self.cloud_api_token = cloud_api_token

    def get_devices(self):
        url = BASE_URL + "devices"
        request = requests.get(url, params=dict(access_token=self.cloud_api_token))
        if request.status_code == requests.codes.ok:
            devices = request.json()
            return devices
        else:
            return None


###################################################################################################
# Device Classes

class Device:
    DEVICE_TYPE = "unknown"
    API_DEVICE_URL = Template(BASE_URL + "devices/$device_id/")
    API_GET_URL = Template(BASE_URL + "devices/$device_id/$var_name")
    API_FUNC_URL = Template(BASE_URL + "devices/$device_id/$func_name")
    API_VITALS_URL = Template(BASE_URL + "diagnostics/$device_id/last")


class Photon(Device):
    DEVICE_TYPE = "Photon"

    def __init__(self, device_id, cloud_api_token):
        self.device_id = device_id
        self.cloud_api_token = cloud_api_token
        self.name = None
        self.tags = None
        self.variables = None
        self.variable_state = None

    def get_data(self):
        pass

    def device_health(self):
        raise NotImplementedError

    def _get_variable_names(self):
        """Queries the variables available with this device"""

    def _get_variable(self, var):
        """Returns the current device state as a JSON formatted string"""
        if var not in self.variables:
            return dict()
        val = send_get_request(url=Device.API_GET_URL.substitute(dict(device_id=self.device_id, var_name=var)),
                               params=dict(access_token=self.cloud_api_token))
        return val

    def _get_state(self):
        print("Querying the device state. Will take ~15s")
        state = dict()
        for var in self.variables:
            state[var] = self._get_variable(var)
        return state

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

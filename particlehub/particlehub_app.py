from flask import Flask, render_template, request, jsonify, make_response
from models import ParticleCloud, Device, HubManager
from secrets import cloud_api_token, log_config, web_host


app = Flask(__name__)
app.config['DEBUG'] = True

cloud = ParticleCloud(cloud_api_token)
hub_manager = HubManager(cloud_api_token)


@app.route('/')
def root():
    return render_template('particlehub.html')


@app.route('/get-devices')
def get_devices():
    devices = cloud.get_devices()
    return make_response(jsonify(devices), 200)


@app.route('/get-device-info')
def get_device_info():
    device_id = request.args.get('device_id')
    device = hub_manager.devices[device_id]
    device_info = device.full_device_data()
    return make_response(jsonify(device_info), 200)


@app.route('/add-device')
def add_device():
    log_source = request.args.get('log_source')
    device_id = request.args.get('device_id')
    device = hub_manager.devices[device_id]
    log_credentials = log_config[log_source]
    hub_manager.add_log_manager(device, log_source, log_credentials)
    return make_response("success", 200)


if __name__ == '__main__':
    app.run(debug=True, host=web_host)

from flask import Flask, render_template, request, jsonify, make_response
from particlehub.models import ParticleCloud, HubManager, LogStopError, LogStartError, StateNotFoundError
from particlehub.secrets import cloud_api_token, log_config, web_host, default_log_source


app = Flask(__name__)
app.config['DEBUG'] = True

cloud = ParticleCloud(cloud_api_token)

try:
    hub_manager = HubManager.from_state_file(cloud_api_token)
except StateNotFoundError:
    hub_manager = HubManager(cloud_api_token)


@app.route('/')
def root():
    return render_template('particlehub.html')


@app.route('/get-devices')
def get_devices():
    devices = hub_manager.devices
    if devices is None:
        return make_response("<h3>No Devices Found</h3>", 200)
    response = ""
    for device_id, device in devices.items():
        response = response + render_template('device_list_row.html', device=device) + "\n"
    return make_response(response, 200)


@app.route('/refresh-all-devices')
def refresh_all_devices():
    hub_manager.update_device_list()
    return get_devices


@app.route('/get-device-info')
def get_device_info():
    device_id = request.args.get('id')
    device = hub_manager.devices[device_id]
    device_info = device.full_device_data()
    response = render_template("device_info.html", device_info=device_info)
    return make_response(response, 200)


@app.route('/add-device')
def add_device():
    log_source = request.args.get('log_source')
    device_id = request.args.get('id')
    _add_device(device_id, log_source)
    return make_response("success", 200)


@app.route('/add-unmanaged-devices')
def add_unmanaged_devices():
    for device_id, device in hub_manager.devices.items():
        if device.log_managed is not True:
            _add_device(device.id, default_log_source)
    return make_response("success", 200)


def _add_device(device_id, log_source):
    device = hub_manager.devices[device_id]
    log_credentials = log_config[log_source]
    hub_manager.add_log_manager(device, log_source, log_credentials)


# TODO: remove_device nomenclature is confusing. Should be remove_log_manager or something.
@app.route('/remove-device')
def remove_device():
    device_id = request.args.get('id')
    _remove_device(device_id)
    return make_response("success", 200)


def _remove_device(device_id):
    hub_manager.remove_log_manager(device_id)


@app.route('/add-tag')
def add_tag():
    device_id = request.args.get('id')
    tag = request.args.get('tag')
    device = hub_manager.devices[device_id]
    device.tags[tag] = None
    hub_manager.save_state()
    return make_response(jsonify(dict(status="success", tag=tag)), 200)

# TODO: Add a remove-tag endpoint


@app.route('/start-logging-device')
def start_logging_device():
    try:
        device_id = request.args.get('id')
        _start_logging_device(device_id)
        return make_response(jsonify({"result": "success"}), 200)
    except LogStartError:
        return make_response(jsonify({"result": "fail"}), 200)


def _start_logging_device(device_id):
    try:
        log_manager = hub_manager.log_managers[device_id]
        log_manager.start_logging()
    except KeyError:
        return make_response(jsonify({"result": "fail",
                                      "message": "Log manager does not exist. Check if device is being managed"}), 200)


@app.route('/stop-logging-device')
def stop_logging_device():
    try:
        device_id = request.args.get('id')
        _stop_logging_device(device_id)
        return make_response(jsonify({"result": "success"}), 200)
    except LogStopError:
        return make_response(jsonify({"result": "fail"}), 200)


def _stop_logging_device(device_id):
    try:
        log_manager = hub_manager.log_managers[device_id]
        log_manager.stop_logging()
    except KeyError:
        pass


@app.route('/start-logging-all')
def start_logging_all():
    try:
        for device_id, device in hub_manager.devices.items():
            _start_logging_device(device.id)
        return make_response(jsonify({"result": "success"}), 200)
    except LogStartError:
        return make_response(jsonify({"result": "fail"}), 200)


@app.route('/stop-logging-all')
def stop_logging_all():
    print("stopping all logging")
    try:
        for device_id, device in hub_manager.devices.items():
            _stop_logging_device(device.id)
        return make_response(jsonify({"result": "success"}), 200)
    except LogStopError:
        return make_response(jsonify({"result": "fail"}), 200)


if __name__ == '__main__':
    app.run(debug=True, host=web_host)

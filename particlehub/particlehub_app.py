import os
import sys
import signal
import logging.handlers
import importlib.util
from flask_wtf import CSRFProtect
from flask import Flask, render_template, request, make_response
from particlehub import models

spec = importlib.util.spec_from_file_location("phconfig", os.getenv("PHCONFIG_FILE"))
phconfig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phconfig)

app = Flask(__name__)
app.secret_key = phconfig.csrf_key
csrf = CSRFProtect()
csrf.init_app(app)

phlog = logging.getLogger('particle-hub')
phlog.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
syslog_handler = logging.handlers.SysLogHandler(address=phconfig.syslog_host)
syslog_handler.setFormatter(log_formatter)
phlog.addHandler(syslog_handler)
models.phlog = phlog

db_log_dest = phconfig.default_log_source
db_log_credentials = phconfig.log_config[db_log_dest]


def stop_signal_handler(signum, frame):
    phlog.info("Exiting")
    sys.exit(0)


signal.signal(signal.SIGINT, stop_signal_handler)
signal.signal(signal.SIGTERM, stop_signal_handler)


@app.route('/', methods=['GET'])
def root():
    # FIXME: Refreshing overwrites the device list, and any updates to each device, like is_managed
    # refresh_all_devices()
    return render_template('particlehub.html')


@app.route('/get-devices', methods=['GET'])
def get_devices():
    devices = hub_manager.devices
    if devices is None:
        return make_response("<h3>No Devices Found</h3>", 200)
    response = ""
    for device_id, device in devices.items():
        response = response + render_template('device_list_row.html', device=device) + "\n"
    return make_response(response, 200)


@app.route('/refresh-all-devices', methods=['GET'])
def refresh_all_devices():
    hub_manager.update_device_list()
    return get_devices()


@app.route('/get-device-info', methods=['GET'])
def get_device_info():
    device_id = request.args.get('id')
    device = hub_manager.devices[device_id]
    device_info = device.full_device_data()
    response = render_template("device_info.html", device_info=device_info)
    return make_response(response, 200)


@app.route('/add-unmanaged-devices', methods=['POST'])
def add_unmanaged_devices():
    for device_id, device in hub_manager.devices.items():
        if device.is_managed is not True:
            _add_device(device.id)
    return make_response("success", 200)
    

@app.route('/add-device', methods=['POST'])
def add_device():
    device_id = request.form['id']
    _add_device(device_id)
    return make_response("success", 200)


def _add_device(device_id):
    hub_manager.add_device(device_id)
    phlog.info("Device Added (id: %s)" % device_id)


@app.route('/remove-device', methods=['POST'])
def remove_device():
    device_id = request.form['id']
    _remove_device(device_id)
    return make_response("success", 200)


def _remove_device(device_id):
    hub_manager.remove_device(device_id)
    phlog.info("Device and log manager removed (id: %s)" % device_id)


@app.route('/update-console', methods=['GET'])
def update_console(n_events=10):
    query_func = models.log_query_functions[db_log_dest]
    points = query_func(db_log_credentials, n_items=n_events)
    html_head = """
    <table class="table table-hover" aria-label="Log console table">
        <thead>
            <tr>
                <th scope="col">Timestamp</th>
                <th scope="col">Data</th>
            </tr>
        </thead>
        <tbody>
    """
    html_table = ""
    for point in points:
        row = "<tr><td>%s</td><td>" % point["time"]
        for k, v in point.iteritems():
            if k != "time":
                row += "%s: %s" % k, v
        row += "</td></tr>"
        html_table += row
    html_end = """    
        </tbody>
    </table>
    """
    table = html_head + html_table + html_end
    return make_response(table, 200)
    
    
def stream_event_handler(event):
    update_console()

# FIXME: Since the callback is triggered from another thread, it cannot call back directly to flask
event_callbacks = list()
cloud = models.ParticleCloud(phconfig.cloud_api_token)
hub_manager = models.HubManager(cloud, phconfig.stream_config, event_callbacks, db_log_dest, db_log_credentials)


if __name__ == '__main__':
    phlog.info("Starting particle-hub")
    app.run(debug=True, host=phconfig.web_host)

from flask import Flask, render_template, request, jsonify
from models import ParticleCloud, Photon
from secrets import cloud_api_token

# Temp variables
web_host = '0.0.0.0'

app = Flask(__name__)
app.config['DEBUG'] = True

cloud = ParticleCloud(cloud_api_token)


@app.route('/')
def main():
    return render_template('particlehub.html')


@app.route('/get-devices')
def get_devices():
    devices = cloud.get_devices()
    return jsonify(devices)


@app.route('get-device-info')
def get_device_info():
    pass


if __name__ == '__main__':
    app.run(debug=True, host=web_host)

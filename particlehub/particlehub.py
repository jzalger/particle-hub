from flask import Flask, render_template, request, jsonify

# Temp variables
web_host = '0.0.0.0'

particlehub_app = Flask(__name__)
particlehub_app.config['DEBUG'] = True


@particlehub_app.route('/')
def main():
    return render_template('particlehub.html')


if __name__ == '__main__':
    particlehub_app.run(debug=True, host=web_host)

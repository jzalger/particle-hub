from flask import Flask, render_template, request, jsonify

# Temp variables
web_host = '0.0.0.0'

particlehub = Flask(__name__)
particlehub.config['DEBUG'] = True


@particlehub.route('/')
def main():
    return render_template('particlehub.html')


if __name__ == '__main__':
    particlehub.run(debug=True, host=web_host)

from flask import Flask, render_template, request, jsonify

# Temp variables
web_host = '0.0.0.0'

app = Flask(__name__)
app.config['DEBUG'] = True


@app.route('/')
def main():
    return render_template('particlehub.html')


if __name__ == '__main__':
    app.run(debug=True, host=web_host)

from flask import Flask

app = Flask(__name__)

@app.route("/v1/test")
def hello_world():
    return "<p>Hello, World!</p>"
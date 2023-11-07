from flask import Flask
import os

app = Flask(__name__)

@app.route("/v1/test")
def hello_world():
    return "<p>Hello, World!</p>"

if __name__ == "__main__":
   app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 5000)))
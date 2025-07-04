from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello from Railway! The new deployment is working.'

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)

CORS(app)

# get all 
@app.route("/test")
def get_all():
    return "Test"


if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    app.run(host='0.0.0.0', port=5005, debug=True)
    # app.run(port=5008, debug=True) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart

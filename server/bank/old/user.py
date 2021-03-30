from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ
import uuid
import base64

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/cs301_team1_bank'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/cs301_team1_bank'
# app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
CORS(app)

class BankUser(db.Model):
    __tablename__ = 'bank_user'
 
    user_id = db.Column(db.String(120), primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    points = db.Column(db.Integer, nullable=False)
 
    def __init__(self, username, firstname, lastname, password, email, points):
        self.user_id = str(base64.b64encode(uuid.uuid1().bytes).decode('ascii')).split("/")[0]
        self.username = username
        self.firstname = firstname
        self.lastname = lastname
        self.password = password
        self.email = email
        self.points = points
 
    def json(self):
        return {"user_id": self.user_id, "username": self.username, "firstname": self.firstname, "lastname": self.lastname, "password": self.password, "email": self.email, "points": self.points}

# get all 
@app.route("/bank/user")
def get_all():
    # query for all user
	return jsonify({"user": [user.json() for user in BankUser.query.all()]})
    
#get user details with user ID
@app.route("/bank/user/<string:UserId>")
def find_by_userId(UserId):
    user_detail = BankUser.query.filter_by(user_id=UserId).all()
    if user_detail:
        return jsonify({"user": [user.json() for user in BankUser.query.filter_by(user_id = UserId)]})
    return jsonify({"message": "User not found."}), 404

#login
@app.route("/bank/login", methods=['POST'])
def login():
    data = request.get_json()
    user_detail = BankUser.query.filter_by(username=data['username']).first()

    if user_detail:
        if user_detail.password == data['password']:
            return jsonify({"message": "Success", "status": 200, "userId": user_detail.user_id}), 200
    return jsonify({"message": "Invalid Username/Password", "status": 404}), 404

  
@app.route("/bank/user/create", methods=['POST'])
def create_user():

    data = request.get_json()
    user_detail = BankUser(**data)
   
    try:
        db.session.add(user_detail)
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred creating the user."}), 500

    return jsonify(user_detail.json()), 201

@app.route("/bank/user/update/<string:UserId>", methods=['POST'])
def update_user(UserId):
    user_detail = BankUser.query.filter_by(user_id=UserId).first()
    data = request.get_json()

    if "username" in data:
        user_detail.username = data["username"]

    if "password" in data:
        user_detail.password = data["password"]

    if "email" in data:
        user_detail.email = data["email"]

    if "points" in data:
        user_detail.points = data["points"]
    
    try:
        db.session.commit()
        
    except:
        return jsonify({"message": "An error occurred updating the user."}),500

    return jsonify(user_detail.json()),201


if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(port=5002, debug=True) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart

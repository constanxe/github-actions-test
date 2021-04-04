from datetime import datetime
from datetime import timedelta
from datetime import timezone

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ

from flask_jwt_extended import jwt_required, JWTManager


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/cs301_team1_bank'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/cs301_team1_bank'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = "9da6905a-7dfe-4fd9-9c1a-63d2fe111c86"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)


db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

class BankLoyaltyUser(db.Model):
    __tablename__ = 'bank_loyalty_user'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(120), nullable=False)
    loyalty_id = db.Column(db.String(80), nullable=False)
    member_id = db.Column(db.String(80), nullable=False)
 
    def __init__(self, user_id, loyalty_id, member_id):
        self.user_id = user_id
        self.loyalty_id = loyalty_id
        self.member_id = member_id
 
    def json(self):
        return {"user_id": self.user_id, "loyalty_id": self.loyalty_id, "member_id": self.member_id}

# get all 
@app.route("/bank/loyalty/user")
@jwt_required(fresh=True)
def get_all():
    # query for all user
	return jsonify({"loyalty_user": [loyalty_user.json() for loyalty_user in BankLoyaltyUser.query.all()]})
    
#get user details with user ID
@app.route("/bank/loyalty/user/<string:userId>")
@jwt_required(fresh=True)
def find_by_userId(userId):
    user_detail = BankLoyaltyUser.query.filter_by(user_id=userId).all()
    if user_detail:
        return jsonify({"loyalty_user": [loyalty_user.json() for loyalty_user in BankLoyaltyUser.query.filter_by(user_id = userId)]})
    return jsonify({"message": "No records"}), 404

#get user details with user_id and loyalty_id
@app.route("/bank/loyalty/user/<string:userId>/<string:loyaltyId>")
@jwt_required(fresh=True)
def find_by_userId_loyaltyId(userId, loyaltyId):

    user_detail = BankLoyaltyUser.query.filter_by(user_id=userId).filter_by(loyalty_id=loyaltyId).all()
    if user_detail:
        return jsonify({"loyalty_user": [loyalty_user.json() for loyalty_user in BankLoyaltyUser.query.filter_by(user_id=userId).filter_by(loyalty_id=loyaltyId)]})
    return jsonify({"message": "No records"}), 404

@app.route("/bank/loyalty/user/create", methods=['POST'])
@jwt_required(fresh=True)
def create_user_loyalty():

    data = request.get_json()
    user_loyalty_detail = BankLoyaltyUser(**data)
   
    try:
        db.session.add(user_loyalty_detail)
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred linking user to loyalty."}), 500

    return jsonify(user_loyalty_detail.json()), 201

@app.route("/bank/loyalty/user/update/<string:userId>/<string:loyaltyId>", methods=['POST'])
@jwt_required(fresh=True)
def update_user_loyalty(userId, loyaltyId):

    data = request.get_json()
    user_loyalty_detail = BankLoyaltyUser.query.filter_by(user_id=userId).filter_by(loyalty_id=loyaltyId).first()

    if "member_id" in data:
        user_loyalty_detail.member_id = data["member_id"]
   
    try:
        db.session.commit()
        
    except:
        return jsonify({"message": "An error occurred updating the record."}),500

    return jsonify(user_loyalty_detail.json()), 201

@app.route("/bank/loyalty/user/delete/<string:userId>/<string:loyaltyId>", methods=['POST'])
@jwt_required(fresh=True)
def delete_user_loyalty(userId, loyaltyId):

    data = request.get_json()
    user_loyalty_detail = BankLoyaltyUser.query.filter_by(user_id=userId).filter_by(loyalty_id=loyaltyId).first()
   
    try:
        db.session.delete(user_loyalty_detail)
        db.session.commit()
        
    except:
        return jsonify({"message": "An error occurred updating the record."}),500

    return jsonify(user_loyalty_detail.json()), 201


if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    app.run(host='0.0.0.0', port=5008, debug=True)
    # app.run(port=5008, debug=True) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart

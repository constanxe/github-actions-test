from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/cs301_team1_ascenda'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://USERNAME:PASSWORD@ascenda-loyalty.canszqrplode.us-east-1.rds.amazonaws.com/cs301_team1_ascenda'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
CORS(app)

class AscendaLoyalty(db.Model):
    __tablename__ = 'ascenda_loyalty'

    loyalty_id = db.Column(db.String(120), primary_key=True)
    loyalty_name = db.Column(db.String(120), unique=True, nullable=False)
    loyalty_unit = db.Column(db.String(120), unique=True, nullable=False)
    processing_time = db.Column(db.String(120), unique=False, nullable=False)
    description = db.Column(db.String(120), unique=False, nullable=False)
    enrollment_link = db.Column(db.String(120), unique=False, nullable=False)
    terms_link = db.Column(db.String(120), unique=False, nullable=False)
    validation = db.Column(db.String(120), unique=False, nullable=True)

    def __init__(self, loyalty_id, loyalty_name, loyalty_unit, processing_time, description, enrollment_link, terms_link, validation):
        self.loyalty_id = loyalty_id
        self.loyalty_name = loyalty_name
        self.loyalty_unit = loyalty_unit
        self.processing_time = processing_time
        self.description = description
        self.enrollment_link = enrollment_link
        self.terms_link = terms_link
        self.validation = validation

    def json(self):
        return {"loyalty_id": self.loyalty_id, "loyalty_name": self.loyalty_name, "loyalty_unit": self.loyalty_unit, "processing_time": self.processing_time, "description": self.description, "enrollment_link": self.enrollment_link, "terms_link": self.terms_link, "validation": self.validation}


# get all loyalty
@app.route("/ascenda/loyalty")
def get_all_loyalty():
    # query for all loyalty programmes
	return jsonify({"loyalty_programme": [loyalty.json() for loyalty in AscendaLoyalty.query.all()]})

# get loyalty programme details with loyalty ID
@app.route("/ascenda/loyalty/<string:LoyaltyId>")
def find_by_loyaltyId(LoyaltyId):
    loyalty_info = AscendaLoyalty.query.filter_by(loyalty_id=LoyaltyId).all()
    if loyalty_info:
        return jsonify({"loyalty_programme": [loyalty.json() for loyalty in AscendaLoyalty.query.filter_by(loyalty_id=LoyaltyId)]})
    return jsonify({"message": "Loyalty programme not found."}), 404

# create a new loyalty programme with details passed in 
@app.route("/ascenda/loyalty/<string:LoyaltyId>/", methods=['POST'])
def create_loyalty(LoyaltyId):
    if (AscendaLoyalty.query.filter_by(loyalty_id=LoyaltyId).first()):
        return jsonify({"message": "The loyalty programme already exists."}), 400

    data = request.get_json()
    loyalty_info = AscendaLoyalty(LoyaltyId, **data)
   
    try:
        db.session.add(loyalty_info)
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred creating the loyalty programme."}), 500

    return jsonify(loyalty_info.json()), 201

# update loyalty programme with loyalty ID
@app.route("/ascenda/loyalty/update/<string:LoyaltyId>/", methods=['POST'])
def update_loyalty(LoyaltyId):
    loyalty_info = AscendaLoyalty.query.filter_by(loyalty_id=LoyaltyId).first()
    data = request.get_json()

    if "loyalty_name" in data:
        loyalty_info.loyalty_name = data["loyalty_name"]
    if "loyalty_unit" in data:
        loyalty_info.loyalty_unit = data["loyalty_unit"]
    if "processing_time" in data:
        loyalty_info.processing_time = data["processing_time"]
    if "description" in data:
        loyalty_info.description = data["description"]
    if "enrollment_link" in data:
        loyalty_info.enrollment_link = data["enrollment_link"]
    if "terms_link" in data:
        loyalty_info.terms_link = data["terms_link"]
    if "validation" in data:
        loyalty_info.validation = data["validation"]

    try:
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred updating the loyalty programme."}),500

    return jsonify(loyalty_info.json()),201

# Loyalty Membership Validation
@app.route("/ascenda/loyalty/membership/<string:LoyaltyId>/<string:MembershipID>")
def membership_validation(LoyaltyId, MembershipID):
    loyalty_info = AscendaLoyalty.query.filter_by(loyalty_id=LoyaltyId).first()

    if loyalty_info:
        validation_pattern = loyalty_info.validation
        print(validation_pattern)
        if re.fullmatch(validation_pattern, MembershipID):
            return jsonify({"result": True}), 201
        return jsonify({"result": False}), 400

    return jsonify({"message": "Loyalty programme not found."}), 404

# delete loyalty record
@app.route("/ascenda/loyalty/delete/<string:LoyaltyId>")
def delete_loyalty(LoyaltyId):
    loyalty_detail = AscendaLoyalty.query.filter_by(loyalty_id=LoyaltyId).first()
   
    try:
        db.session.delete(loyalty_detail)
        db.session.commit()
        
    except:
        return jsonify({"message": "An error occurred updating the record."}),500

    return jsonify(loyalty_detail.json()), 201

if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5006, debug=True) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart
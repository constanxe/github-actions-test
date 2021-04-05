from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/cs301_team1_ascenda'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://admin:itsaadmin@ascenda-bank.cq4bzcmfnjpo.us-east-1.rds.amazonaws.com/cs301_team1_ascenda'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
CORS(app)

class AscendaBank(db.Model):
    __tablename__ = 'ascenda_bank'
 
    bank_id = db.Column(db.VARCHAR(100), primary_key=True)
    bank_name = db.Column(db.String(80), nullable=False)
    bank_unit = db.Column(db.String(80), nullable=False)
 
    def __init__(self, bank_id, bank_name, bank_unit):
        self.bank_id = bank_id
        self.bank_name = bank_name
        self.bank_unit = bank_unit

    def json(self):
        return {"bank_id": self.bank_id, "bank_name": self.bank_name, "bank_unit": self.bank_unit}

# get all 
@app.route("/ascenda/bank")
def get_all():
    # query for all bank
	return jsonify({"bank": [bank.json() for bank in AscendaBank.query.all()]})
    
#get user details with user ID
@app.route("/ascenda/bank/<string:BankId>")
def find_by_bankId(BankId):
    bank_detail = AscendaBank.query.filter_by(bank_id=BankId).all()
    if bank_detail:
        return jsonify({"bank": [bank.json() for bank in AscendaBank.query.filter_by(bank_id = BankId)]})
    return jsonify({"message": "Bank not found."}), 404
  
@app.route("/ascenda/bank/<string:BankId>/", methods=['POST'])
def create_bank(BankId):
    if (AscendaBank.query.filter_by(bank_id=BankId).first()):
        return jsonify({"message": "The bank already exists."}), 400

    data = request.get_json()
    bank_detail = AscendaBank(BankId, **data)
   
    try:
        db.session.add(bank_detail)
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred creating the bank."}), 500

    return jsonify(bank_detail.json()), 201

@app.route("/ascenda/bank/update/<string:BankId>/", methods=['POST'])
def update_bank(BankId):
    bank_detail = AscendaBank.query.filter_by(bank_id=BankId).first()
    data = request.get_json()

    if "bank_name" in data:
        bank_detail.bank_name = data["bank_name"]

    if "bank_unit" in data:
        bank_detail.bank_unit = data["bank_unit"]
    
    try:
        db.session.commit()
        
    except:
        return jsonify({"message": "An error occurred updating the bank."}),500

    return jsonify(bank_detail.json()),201


if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host="0.0.0.0", port=5001, debug=True) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart
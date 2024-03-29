from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import uuid
import base64
import requests
import csv
from datetime import datetime
import time
from apscheduler.schedulers.background import BackgroundScheduler
import os

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/cs301_team1_ascenda'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://admin:itsaadmin@ascenda-transaction.cq4bzcmfnjpo.us-east-1.rds.amazonaws.com/cs301_team1_ascenda'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["dbURL"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

class AscendaTransaction(db.Model):
    __tablename__ = 'ascenda_transaction'

    reference_num = db.Column(db.String(120), primary_key=True)
    loyalty_id = db.Column(db.String(120), nullable=False)
    member_id = db.Column(db.String(120), nullable=False)
    member_name_first = db.Column(db.String(80), nullable=False)
    member_name_last = db.Column(db.String(80), nullable=False)
    transaction_date = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    partner_code = db.Column(db.String(120), nullable=False)
    bank_user_id = db.Column(db.String(120), nullable=False)
    additional_info = db.Column(db.String(1000), nullable=True)
    outcome_code = db.Column(db.Integer, nullable=True)

    def __init__(self, reference_num, loyalty_id, member_id, member_name_first, member_name_last, transaction_date, amount, partner_code, bank_user_id, additional_info, outcome_code):
        self.reference_num = reference_num
        self.loyalty_id = loyalty_id
        self.member_id = member_id
        self.member_name_first = member_name_first
        self.member_name_last = member_name_last
        self.transaction_date = transaction_date
        self.amount = amount
        self.partner_code = partner_code
        self.bank_user_id = bank_user_id
        self.additional_info = additional_info
        self.outcome_code = outcome_code

    def json(self):
        return {"reference_num": self.reference_num, "loyalty_id": self.loyalty_id, "member_id": self.member_id, "member_name_first": self.member_name_first, "member_name_last": self.member_name_last, "transaction_date": self.transaction_date, "amount": self.amount, "partner_code": self.partner_code, "bank_user_id": self.bank_user_id, "additional_info": self.additional_info, "outcome_code": self.outcome_code}


# get all transaction
@app.route("/ascenda/transaction")
def get_all_transaction():
    # query for all transaction
	return jsonify({"transaction": [transaction.json() for transaction in AscendaTransaction.query.all()]})

# get all partner code
@app.route("/ascenda/transaction/partner")
def get_all_partnercode():
    partnercodes = list(set([transaction for transaction in AscendaTransaction.query.filter_by(outcome_code=0).with_entities(AscendaTransaction.partner_code).all()]))
    processed = tuple([item for t in partnercodes for item in t])
    return jsonify(processed)

# get all transaction with PartnerCode
@app.route("/ascenda/transaction/partner/<string:PartnerCode>")
def find_by_partnerCode(PartnerCode):
    transaction_info = AscendaTransaction.query.filter_by(partner_code=PartnerCode).all()
    if (request.json) != None:
        transaction_info = AscendaTransaction.query.filter_by(partner_code=PartnerCode).filter(AscendaTransaction.reference_num.in_(request.json)).all()
    if transaction_info:
        return jsonify({"transaction": [transaction.json() for transaction in transaction_info]})
    return jsonify({"transaction": [] })

# get transaction details with ID
@app.route("/ascenda/transaction/<string:TransactionId>")
def find_by_transactionId(TransactionId):
    transaction_info = AscendaTransaction.query.filter_by(reference_num=TransactionId).all()

    if transaction_info:
        return jsonify({"transaction": [transaction.json() for transaction in AscendaTransaction.query.filter_by(reference_num=TransactionId)]})
    return jsonify({"message": "Transaction not found."}), 404

# create a new transaction with details passed in 
@app.route("/ascenda/transaction/create", methods=['POST'])
def create_transaction():
    # if (AscendaTransaction.query.filter_by(id=TransactionId).first()):
    #     return jsonify({"message": "The transaction already exists."}), 400
    reference_num = str(base64.b64encode(uuid.uuid1().bytes).decode('ascii')).split("/")[0][:10].upper()
    inputData = request.get_json()
    transaction_info = AscendaTransaction(reference_num, **inputData)
   
    try:
        db.session.add(transaction_info)
        db.session.commit()

        try:
            dynamo = requests.post('https://0c0q71flo8.execute-api.us-east-1.amazonaws.com/test/polling', 
                                json = {
                                    "reference_num": reference_num,
                                    "loyalty_id": inputData["loyalty_id"],
                                    "partner_code": inputData["partner_code"]
                                })
            
        except Exception as e:
            return jsonify({"message": "Unable to add to Dynamo"}), 500
            
    except Exception as e:
        return jsonify({"message": "Failed to create transaction"}), 500
        # return jsonify({"message": "An error occurred creating the transaction."}), 500

    return jsonify(transaction_info.json()), 200

# update transaction status
@app.route("/ascenda/transaction/update_status/<string:TransactionId>", methods=['POST'])
def update_transaction_status(TransactionId):
    transaction = AscendaTransaction.query.filter_by(reference_num=TransactionId).first()
    data = request.get_json()
    
    transaction.outcome_code=data["outcome_code"]
    
    try:
        db.session.commit()
        
        try:
            url_link = 'https://0c0q71flo8.execute-api.us-east-1.amazonaws.com/test/polling/' + str(transaction.reference_num) + "/" + str(data["outcome_code"])
            dynamo = requests.put(url_link)
        except Exception as e:
            return jsonify(str(e)), 500
        
    except:
        return jsonify({"message": "An error occurred updating the transaction status."}),500

    return jsonify(transaction.json()),200
    
# update transaction with transaction ID
@app.route("/ascenda/transaction/update/<string:TransactionId>/", methods=['POST'])
def update_transaction(TransactionId):
    transaction_info = AscendaTransaction.query.filter_by(reference_num=TransactionId).first()
    data = request.get_json()

    if "loyalty_id" in data:
        transaction_info.loyalty_id = data["loyalty_id"]
    if "member_id" in data:
        transaction_info.member_id = data["member_id"]
    if "member_name_first" in data:
        transaction_info.member_name_first = data["member_name_first"]
    if "member_name_last" in data:
        transaction_info.member_name_last = data["member_name_last"]
    if "transaction_date" in data:
        transaction_info.transaction_date = data["transaction_date"]
    if "amount" in data:
        transaction_info.amount = data["amount"]
    if "partner_code" in data:
        transaction_info.partner_code = data["partner_code"]
    if "bank_user_id" in data:
        transaction_info.bank_user_id = data["bank_user_id"]
    if "additional_info" in data:
        transaction_info.additional_info = data["additional_info"]
    if "outcome_code" in data:
        transaction_info.outcome_code = data["outcome_code"]

    try:
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred updating the transaction."}),500

    return jsonify(transaction_info.json()),200

# delete loyalty transaction record
@app.route("/ascenda/transaction/deleteloyalty/<string:LoyaltyId>")
def delete_transaction_loyalty(LoyaltyId):
    try:
        delete_file = requests.get('http://ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:5008/ascenda/filehandle/delete_loyalty/' + LoyaltyId)
        AscendaTransaction.query.filter_by(loyalty_id=LoyaltyId).delete()
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred deleting the record."}),500

    return jsonify({"message": "Transactions deleted successfully"}), 200

# delete partner transaction record
@app.route("/ascenda/transaction/deletebank/<string:PartnerCode>")
def delete_transaction_partner(PartnerCode):
    try:
        delete_file = requests.get('http://ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:5008/ascenda/filehandle/delete_bank/' + PartnerCode)
        AscendaTransaction.query.filter_by(partner_code=PartnerCode).delete()
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred deleting the record."}),500

    return jsonify({"message": "Transactions deleted successfully"}), 200

# delete partner transaction record
@app.route("/ascenda/transaction/deleterecord/<string:PartnerCode>/<string:BankUserId>")
def delete_transaction(PartnerCode, BankUserId):
    try:
        AscendaTransaction.query.filter_by(partner_code=PartnerCode, bank_user_id=BankUserId).delete()
        delete_file = requests.get('http://ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:5008/ascenda/filehandle/delete_user/' + PartnerCode + "/" + BankUserId)
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred deleting the record."}),500

    return jsonify({"message": "Transaction deleted successfully"}), 201

if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5004, debug=True) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart
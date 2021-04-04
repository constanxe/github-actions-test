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
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/cs301_team1_ascenda'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/cs301_team1_ascenda'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

class AscendaTransaction(db.Model):
    __tablename__ = 'ascenda_transaction'

    id = db.Column(db.String(120), primary_key=True)
    loyalty_id = db.Column(db.String(120), nullable=False)
    member_id = db.Column(db.String(120), nullable=False)
    member_name_first = db.Column(db.String(80), nullable=False)
    member_name_last = db.Column(db.String(80), nullable=False)
    transaction_date = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    reference_num = db.Column(db.String(120), nullable=False)
    partner_code = db.Column(db.String(120), nullable=False)
    bank_user_id = db.Column(db.String(120), nullable=False)
    additional_info = db.Column(db.String(1000), nullable=True)
    outcome_code = db.Column(db.Integer, nullable=True)

    def __init__(self, loyalty_id, member_id, member_name_first, member_name_last, transaction_date, amount, reference_num, partner_code, bank_user_id, additional_info, outcome_code):
        self.id = str(base64.b64encode(uuid.uuid1().bytes).decode('ascii')).split("/")[0]
        self.loyalty_id = loyalty_id
        self.member_id = member_id
        self.member_name_first = member_name_first
        self.member_name_last = member_name_last
        self.transaction_date = transaction_date
        self.amount = amount
        self.reference_num = reference_num
        self.partner_code = partner_code
        self.bank_user_id = bank_user_id
        self.additional_info = additional_info
        self.outcome_code = outcome_code

    def json(self):
        return {"loyalty_id": self.loyalty_id, "member_id": self.member_id, "member_name_first": self.member_name_first, "member_name_last": self.member_name_last, "transaction_date": self.transaction_date, "amount": self.amount, "reference_num": self.reference_num, "partner_code": self.partner_code, "bank_user_id": self.bank_user_id, "additional_info": self.additional_info, "outcome_code": self.outcome_code}


# get all transaction
@app.route("/ascenda/transaction")
def get_all_transaction():
    # query for all transaction
	return jsonify({"transaction": [transaction.json() for transaction in AscendaTransaction.query.all()]})

# get all transaction
@app.route("/ascenda/transaction/<string:PartnerCode>")
def find_by_partnerCode(PartnerCode):
    transaction_info = AscendaTransaction.query.filter_by(partner_code=PartnerCode).filter(AscendaTransaction.reference_num.in_(request.json)).all()
    if transaction_info:
        return jsonify({"transaction": [transaction.json() for transaction in AscendaTransaction.query.filter_by(partner_code=PartnerCode).filter(AscendaTransaction.reference_num.in_(request.json))]})

# get transaction details with ID
@app.route("/ascenda/transaction/<string:TransactionId>")
def find_by_transactionId(TransactionId):
    transaction_info = AscendaTransaction.query.filter_by(id=TransactionId).all()

    if transaction_info:
        return jsonify({"transaction": [transaction.json() for transaction in AscendaTransaction.query.filter_by(id=TransactionId)]})
    return jsonify({"message": "Transaction not found."}), 404

# create a new transaction with details passed in 
@app.route("/ascenda/transaction/create", methods=['POST'])
def create_transaction():
    # if (AscendaTransaction.query.filter_by(id=TransactionId).first()):
    #     return jsonify({"message": "The transaction already exists."}), 400

    data = request.get_json()
    transaction_info = AscendaTransaction(**data)
   
    try:
        db.session.add(transaction_info)
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred creating the transaction."}), 500

    return jsonify(transaction_info.json()), 201

# delete transaction record
@app.route("/ascenda/transaction/delete/<string:ReferenceNum>")
def delete_transaction(ReferenceNum):

    transaction_detail = AscendaTransaction.query.filter_by(reference_num=ReferenceNum).first()
   
    try:
        db.session.delete(transaction_detail)
        db.session.commit()
        
    except:
        return jsonify({"message": "An error occurred updating the record."}),500

    return jsonify(transaction_detail.json()), 201

# update transaction with transaction ID
@app.route("/ascenda/transaction/update/<string:TransactionId>/", methods=['POST'])
def update_transaction(TransactionId):
    transaction_info = AscendaTransaction.query.filter_by(id=TransactionId).first()
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
    if "reference_num" in data:
        transaction_info.reference_num = data["reference_num"]
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

    return jsonify(transaction_info.json()),201

# send accrual to S3
# @app.route("/ascenda/transaction/send_accrual/", methods=['POST'])
def send_accrual(*args, **kwargs):
    with app.app_context():
        try:
            response = requests.get('http://localhost:5006/ascenda/loyalty')
            response_data = response.json()
            loyalty_programs = response_data["loyalty_programme"]

            today = datetime.now()

            for loyalty_program in loyalty_programs:
                transactions = AscendaTransaction.query.filter_by(loyalty_id=loyalty_program["loyalty_id"]).filter_by(outcome_code=0).all()
                file_path = "../accrual_file/" + loyalty_program["loyalty_id"] + "_" + today.strftime("%Y%m%d_%H%M%S") + ".txt"
                with open(file_path, mode="w", newline="") as accrual_file:
                    writer = csv.writer(accrual_file)
                    writer.writerow(["Index", "Member ID", "Member first name", "Member last name", "Transfer date", "Amount", "Reference number", "Partner code"])
                    for index, transaction in enumerate(transactions):
                        transaction_data = transaction.json()
                        writer.writerow([index+1, transaction_data['member_id'], transaction_data['member_name_first'], transaction_data['member_name_last'], transaction_data['transaction_date'], transaction_data['amount'], transaction_data['reference_num'], transaction_data['partner_code']])
                        # change the code to 1010 indicates that it is processing
                        transaction.outcome_code = "1010"
                        db.session.commit()

            print ("done")
        except:
            print("error")
            return jsonify({"message": "An error occurred while processing the accrual"}), 500


        return jsonify({"message": "Success"}), 201

app.scheduler = BackgroundScheduler()
app.scheduler.add_job(send_accrual, "cron", day_of_week='0-6', hour=20, minute=0)
app.scheduler.start()

# process handback files
# @app.route("/ascenda/transaction/process_handback/", methods=['POST'])
def process_handback():
    with app.app_context():
        try:
            response = requests.get('http://localhost:5006/ascenda/loyalty')
            response_data = response.json()
            loyalty_programs = response_data["loyalty_programme"]

            directory = r'..\handback_file'
            for filename in os.listdir(directory):
                if filename.endswith(".txt"):
                    with open(os.path.join(directory, filename), newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        next(reader) # Skip headers
                        for transaction_data in reader:
                            transaction = AscendaTransaction.query.filter_by(reference_num=transaction_data[2]).filter_by(outcome_code=0).first()
                            transaction.outcome_code = transaction_data[3]
                            db.session.commit()
        except:
            print("error")
            return jsonify({"message": "An error occurred while processing the handback"}), 500
    return jsonify({"message": "Success"}), 201

if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(port=5004, debug=True, use_reloader=False) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ
import uuid
import requests, json
import base64

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/cs301_team1_bank'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/cs301_team1_bank'
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
# app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+mysqlconnector://admin:itsaadmin@bank.c8lpmru5pno3.us-east-1.rds.amazonaws.com:3306/cs301_team1_bank"

ascendaUrl = environ.get('ascendaUrl')
# ascendaUrl = "http://ascenda-lb-1398984097.us-east-1.elb.amazonaws.com"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
CORS(app)

class BankTransaction(db.Model):
    __tablename__ = 'bank_transaction'
 
    reference_num = db.Column(db.String(120),primary_key=True)
    loyalty_id = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.String(120), nullable=False)
    member_id = db.Column(db.String(120), nullable=False)
    transaction_date = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    additional_info = db.Column(db.String(1000), nullable=True)
    outcome_code = db.Column(db.Integer, nullable=True)
 
    def __init__(self, loyalty_id, user_id, member_id, transaction_date, amount, outcome_code, additional_info = None):
        self.reference_num = str(base64.b64encode(uuid.uuid1().bytes).decode('ascii')).split("/")[0]
        self.loyalty_id = loyalty_id
        self.user_id = user_id
        self.member_id = member_id
        self.transaction_date = transaction_date
        self.amount = amount
        self.additional_info = additional_info
        self.outcome_code = outcome_code
 
    def json(self):
        return {"reference_num": self.reference_num, "loyalty_id": self.loyalty_id, "user_id": self.user_id, "member_id": self.member_id, "transaction_date": self.transaction_date, "amount": self.amount, "additional_info": self.additional_info, "outcome_code" : self.outcome_code}

# get all 
@app.route("/bank/transaction")
def get_all():
    # query for unfulfilled
    unfulfilled_transactions = BankTransaction.query.filter(BankTransaction.outcome_code.is_(None)).all()
    return jsonify({"transaction" : [transaction.json() for transaction in BankTransaction.query.all()] })

    transactionRefs = json.dumps([transaction.reference_num for transaction in unfulfilled_transactions])
    url = ascendaUrl + ':5004/ascenda/transaction/BANKABC'
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("GET", url, headers=headers, data=transactionRefs)

    response_data = response.json()


    for transaction in response_data['transaction']:
        data = {"outcome_code" : transaction['outcome_code']}
        transactionId = transaction['reference_num']
        (isUpdated, user_detail) = update_helper(transactionId, data)
    
    # query for all user
    return jsonify({"transaction" : [transaction.json() for transaction in BankTransaction.query.all()] })
    
	# return jsonify({"transaction": [transaction.json() for transaction in BankTransaction.query.all()]})
    
#get transaction details by user ID
@app.route("/bank/transaction/user/<string:UserId>")
def find_by_userId(UserId):
    transaction_detail = BankTransaction.query.filter_by(user_id=UserId).all()
    if transaction_detail:
        return jsonify({"transaction": [transaction.json() for transaction in BankTransaction.query.filter_by(user_id = UserId)]})
    return jsonify({"message": "Transaction not found."}), 404

#get transaction details with transaction ID
@app.route("/bank/transaction/<string:TransactionId>")
def find_by_transactionId(TransactionId):
    transaction_detail = BankTransaction.query.filter_by(reference_num=TransactionId).all()
    if transaction_detail:
        return jsonify({"transaction": [transaction.json() for transaction in BankTransaction.query.filter_by(reference_num = TransactionId)]})
    return jsonify({"message": "Transaction not found."}), 404
  
@app.route("/bank/transaction/", methods=['POST'])
def create_transaction():
    data = request.get_json()
    transaction_detail = BankTransaction(**data)
    test = ""
   
    try:
        db.session.add(transaction_detail)
        db.session.commit()
    except Exception as e:
        print (e)
        return jsonify({"message": str(e)}), 500
        # return jsonify({"message": "An error occurred creating the transaction."}), 500

    return jsonify(transaction_detail.json()), 201

# delete transaction record
@app.route("/bank/transaction/delete/<string:transactionId>")
def delete_transaction(transactionId):

    transaction_detail = BankTransaction.query.filter_by(reference_num=transactionId).first()
   
    try:
        db.session.delete(transaction_detail)
        db.session.commit()
        
    except:
        return jsonify({"message": "An error occurred updating the record."}),500

    return jsonify(transaction_detail.json()), 201

@app.route("/bank/transaction/update/<string:TransactionId>/", methods=['POST'])
def update_transaction(TransactionId):
    
    data = request.get_json()

    (isUpdated, user_detail) = update_helper(TransactionId, data)

    if isUpdated:
        return jsonify(user_detail.json()),201
    return jsonify({"message": "An error occurred updating the transaction."}),500

    

def update_helper(TransactionId, data):
    user_detail = BankTransaction.query.filter_by(reference_num=TransactionId).first()

    if "reference_num" in data:
        user_detail.reference_num = data["reference_num"]

    if "loyalty_id" in data:
        user_detail.loyalty_id = data["loyalty_id"]

    if "user_id" in data:
        user_detail.user_id = data["user_id"]

    if "member_id" in data:
        user_detail.member_id = data["member_id"]

    if "transaction_date" in data:
        user_detail.transaction_date = data["transaction_date"]
        
    if "amount" in data:
        user_detail.amount = data["amount"]

    if "additional_info" in data:
        user_detail.additional_info = data["additional_info"]
    
    try:
        db.session.commit()
        
    except:
        return False, user_detail
    return True, user_detail


if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    app.run(host='0.0.0.0', port=5005, debug=True)
    # app.run(port=5005, debug=True) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ

    app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/cs301_team1_ascenda'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://admin:itsaadmin@ascenda-exchange-rate-db.cq4bzcmfnjpo.us-east-1.rds.amazonaws.com/cs301_team1_ascenda'
# app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
CORS(app)

class AscendaExchangeRate(db.Model):
    __tablename__ = 'ascenda_exchange_rate'
 
    bank_id = db.Column(db.VARCHAR(100), primary_key=True)
    loyalty_id = db.Column(db.VARCHAR(100), primary_key=True)
    base_exchange_amount = db.Column(db.VARCHAR(80), nullable=False)
    loyalty_exchange_amount = db.Column(db.VARCHAR(80), nullable=False)
 
    def __init__(self, bank_id, loyalty_id, base_exchange_amount, loyalty_exchange_amount):
        self.bank_id = bank_id
        self.loyalty_id = loyalty_id
        self.base_exchange_amount = base_exchange_amount
        self.loyalty_exchange_amount = loyalty_exchange_amount
 
    def json(self):
        return {"bank_id": self.bank_id, "loyalty_id": self.loyalty_id, "base_exchange_amount": self.base_exchange_amount, "loyalty_exchange_amount": self.loyalty_exchange_amount}

# get all 
@app.route("/ascenda/exchange_rate")
def get_all():
    # query for all exchange rate
	return jsonify({"exchange_rate": [rate.json() for rate in AscendaExchangeRate.query.all()]})
    
#get exchange rate with bank ID and partner ID
@app.route("/exchange_rate/<string:BankId>/<string:PartnerId>")
def find_by_bankAndPartnerId(BankId, PartnerId):
    exchange_rate = AscendaExchangeRate.query.filter_by(bank_id=BankId, loyalty_id = PartnerId).all()
    if exchange_rate:
        return jsonify({"exchange_rate": [rate.json() for rate in AscendaExchangeRate.query.filter_by(bank_id=BankId, loyalty_id = PartnerId)]})
    return jsonify({"message": "ExchangeRate not found."}), 404

#get exchange rate with bank ID
@app.route("/ascenda/exchange_rate/<string:BankId>")
def find_by_bankId(BankId):
    exchange_rate = AscendaExchangeRate.query.filter_by(bank_id=BankId).all()
    if exchange_rate:
        return jsonify({"exchange_rate": [rate.json() for rate in AscendaExchangeRate.query.filter_by(bank_id=BankId)]})
    return jsonify({"message": "ExchangeRate not found."}), 404

# Create  
@app.route("/ascenda/exchange_rate/<string:BankId>/<string:PartnerId>/", methods=['POST'])
def create_exchange_rate(BankId, PartnerId):
    if (AscendaExchangeRate.query.filter_by(bank_id = BankId, loyalty_id = PartnerId).first()):
        return jsonify({"message": "The exchange rate already exists."}), 400

    data = request.get_json()
    print (data)
    rate_detail = AscendaExchangeRate(BankId, PartnerId, **data)
   
    try:
        db.session.add(rate_detail)
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred creating the exchange rate."}), 500

    return jsonify(rate_detail.json()), 201

@app.route("/ascenda/exchange_rate/update/<string:BankId>/<string:PartnerId>/", methods=['POST'])
def update_rate(BankId, PartnerId):
    rate_detail = AscendaExchangeRate.query.filter_by(bank_id = BankId, loyalty_id = PartnerId).first()
    data = request.get_json()

    if "base_exchange_amount" in data:
        rate_detail.base_exchange_amount = data["base_exchange_amount"]

    if "loyalty_exchange_amount" in data:
        rate_detail.loyalty_exchange_amount = data["loyalty_exchange_amount"]
    
    try:
        db.session.commit()
        
    except:
        return jsonify({"message": "An error occurred updating the exchange rate."}),500

    return jsonify(rate_detail.json()),201


if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5003, debug=True) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart
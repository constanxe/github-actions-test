from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost:3306/cs301_team1_ascenda'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/cs301_team1_ascenda'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
db = SQLAlchemy(app)
CORS(app)

class AscendaLoyaltyUser(db.Model):
    __tablename__ = 'ascenda_loyalty_user'

    member_id = db.Column(db.String(120), primary_key=True)
    amount = db.Column(db.String(120), unique=False, nullable=False)

    def __init__(self, member_id, amount):
        self.member_id = member_id
        self.amount = amount

    def json(self):
        return {"member_id": self.member_id, "amount": self.amount}

# get all loyalty_user
@app.route("/ascenda/loyalty_user")
def get_all_loyalty_user():
    # query for all loyalty users
	return jsonify({"loyalty_user": [loyalty_user.json() for loyalty_user in AscendaLoyaltyUser.query.all()]})

# get loyalty user details with Member ID
@app.route("/ascenda/loyalty_user/<string:MemberId>")
def find_by_memberId(MemberId):
    loyalty_user_info = AscendaLoyaltyUser.query.filter_by(member_id=MemberId).all()
    if loyalty_user_info:
        return jsonify({"loyalty_user": [loyalty_user.json() for loyalty_user in AscendaLoyaltyUser.query.filter_by(member_id=MemberId)]})
    return jsonify({"message": "Loyalty user not found."}), 404

# create a new loyalty user with details passed in 
@app.route("/ascenda/loyalty_user/<string:MemberId>/", methods=['POST'])
def create_loyalty_user(MemberId):
    if (AscendaLoyaltyUser.query.filter_by(member_id=MemberId).first()):
        return jsonify({"message": "The loyalty user already exists."}), 400

    data = request.get_json()
    loyalty_user_info = AscendaLoyaltyUser(MemberId, **data)
   
    try:
        db.session.add(loyalty_user_info)
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred creating the loyalty user."}), 500

    return jsonify(loyalty_user_info.json()), 201

# update loyalty user with member ID
@app.route("/ascenda/loyalty_user/update/<string:MemberId>/", methods=['POST'])
def update_loyalty_user(MemberId):
    loyalty_user_info = AscendaLoyaltyUser.query.filter_by(member_id=MemberId).first()
    data = request.get_json()

    if "amount" in data:
        loyalty_user_info.amount = data["amount"]

    try:
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred updating the loyalty programme."}),500

    return jsonify(loyalty_user_info.json()),201


if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(port=5007, debug=True) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart
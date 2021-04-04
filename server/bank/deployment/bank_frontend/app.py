from flask import Flask, render_template, jsonify, request, redirect, url_for, session, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import requests, json
from os import environ
from functools import wraps
import uuid

from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, template_folder='./client/templates', static_folder='./client/static')
proxyUrl = environ.get('proxyUrl')
ascendaUrl = environ.get('ascendaUrl')
app.config["SECRET_KEY"] = uuid.uuid4().hex


csrf = CSRFProtect(app)
csrf.init_app(app)

CORS(app)
"""
FRONTEND RENDERING ENDPOINTS 
"""

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if  (session['logged_in'] == False):
                return redirect(url_for('login_page'))
            else:
                url = f'{proxyUrl}:5002/checkFresh'
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {session["access_token"]}'
                }
                resp_data = send_request(url, headers, "GET")
                if resp_data["status"] == 401:
                    return redirect(url_for('logout_page'))
                # session["access_token"] = resp_data["access_token"]
        except:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def welcome_page():
    return render_template('bank.html')

@app.route("/transfer_summary")
@login_required
def transfer_summary_page():
    outcome_codes = {
        "0000": "Successful",
        "0001": "Member not found",
        "0002": "Member name mismatch",
        "0003": "Member account closed",
        "0004": "Member account suspended",
        "0005": "Member ineligble for accrual",
        "0099": "Unable to process, please contact support for more information"
    }

    return render_template('transfer_summary.html', data = {'outcome_codes': outcome_codes})

@app.route("/demo_polling")
@login_required
def demo_polling():
    outcome_codes = {
        "0000": "Successful",
        "0001": "Member not found",
        "0002": "Member name mismatch",
        "0003": "Member account closed",
        "0004": "Member account suspended",
        "0005": "Member ineligble for accrual",
        "0099": "Unable to process, please contact support for more information"
    }

    return render_template('admin_transfer_summary.html', data = {'outcome_codes': outcome_codes})

@app.route("/loyalty_programme")
@login_required
def loyalty_programme_page():

    # GET LOYALTY PROGRAMS
    resp = requests.get(f"{ascendaUrl}:5006/ascenda/loyalty")
    loyalties =  json.loads(resp.content)
    programs = []
    for item in loyalties["loyalty_programme"]:
        programs.append(item)

    # GET EXISITING USER MEMBERSHIPS
    membershipUrl = f"{proxyUrl}:5008/bank/loyalty/user/{session['userId']}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session["access_token"]}'
    }
    resp = requests.request("GET", membershipUrl, headers=headers)
    memberships = json.loads(resp.content)

    user_membership = {}
    if "loyalty_user" in memberships:
        for item in memberships["loyalty_user"]:
            user_membership[item["loyalty_id"]] = item["member_id"]

    # GET USER CREDITS
    userUrl = f"{proxyUrl}:5002/bank/user/{session['userId']}"
    resp = requests.request("GET", userUrl, headers=headers)
    user =  json.loads(resp.content)
    
    user = {
        "credits" : user["user"][0]["points"]
    }

    data = {
        'programs' : programs,
        'user_membership' : user_membership,
        'user' : user
    }
    return render_template('loyalty_programme.html', data = data)

@app.route("/login")
def login_page():
    return render_template('login.html')

@app.route("/logout")
def logout_page():
    session.pop('access_token', None)
    session.pop('refresh_token', None)
    session.pop('userId', None)
    session['logged_in'] = False

    return render_template('logout.html')


"""
REDIRECT API ENDPOINTS :: CSRF PROTECTED
MAKE ALL REQUEST FROM SERVER SIDE
NAT INSTANCE ONLY WILL ALLOW INBOUND FROM FRONTEND SG AND BANK API SG
NEED TO TEST IF THIS METHOD WORKS
"""

@app.route("/redirect", methods=['POST'])
# @csrf.exempt
def redirect_helper():
    data = request.get_json()
    if data != None and "action" in data:
        action = data["action"]

        if action == "login":
            resp_data = login_helper(data['payload'])

        elif action == "fetchCurrentUser":
            resp_data = fetch_current_user_helper(data['payload'])

        elif action == "updateCurrentUser":
            resp_data = update_current_user_helper(data['payload'])

        elif action == "createAscendaTransaction": # Ascenda
            resp_data = create_ascenda_transaction_helper(data['payload'])

        elif action == "createBankTransaction":
            resp_data = create_bank_transaction_helper(data['payload'])

        elif action == "fetchCurrentUserTransactions":
            resp_data = fetch_user_bank_transactions_helper(data['payload'])

        elif action == "fetchCurrentUserTransaction":
            resp_data = fetch_user_bank_transaction_helper(data['payload'])
        
        elif action == "fetchAllTransaction":
            resp_data = fetch_all_transactions_helper()

        elif action == "deleteCurrentUserTransaction":
            resp_data = delete_user_bank_transaction_helper(data['payload'])

        elif action == "deleteAscendaTransaction": # Ascenda
            resp_data = delete_ascenda_transaction_helper(data['payload'])

        elif action == "createLoyaltyUser":
            resp_data = create_loyalty_user_helper(data['payload'])

        elif action == "validateMembershipFormat": # Ascenda
            resp_data = validate_membership_helper(data['payload'])

        else:
            return jsonify({"message": 'invalid call'}), 401

        return jsonify(resp_data), resp_data["status"]
    

    return jsonify({"message": 'invalid call'}), 401

def login_helper(payload):
    url = proxyUrl + ':5002/bank/login'
    headers = {
        'Content-Type': 'application/json',
    }

    json_payload = json.dumps(payload)

    resp = requests.request("POST", url, headers=headers, data=json_payload)

    data = resp.json()

    if (resp.status_code != 200):
        return data

    session["access_token"] = data["access_token"]
    session["refresh_token"] = data["refresh_token"]
    session["userId"] = data["userId"]
    session['logged_in'] = True


    return {"userId" : data["userId"], "status": 200}

def fetch_current_user_helper(payload):
    url = f'{proxyUrl}:5002/bank/user/{payload["userId"]}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session["access_token"]}'
    }
    
    return send_request(url, headers, "GET", validate_token=True)

def update_current_user_helper(payload):
    url = f'{proxyUrl}:5002/bank/user/update/{payload["userId"]}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session["access_token"]}'
    }

    json_payload = json.dumps(payload)

    return send_request(url, headers, "POST", json_payload, True)

def create_ascenda_transaction_helper(payload):
    url = f'{ascendaUrl}:5004/ascenda/transaction/create'
    headers = {
        'Content-Type': 'application/json'
    }

    json_payload = json.dumps(payload)

    return send_request(url, headers, "POST", json_payload)

def create_bank_transaction_helper(payload):
    url = f'{proxyUrl}:5005/bank/transaction/'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session["access_token"]}'
    }

    json_payload = json.dumps(payload)

    return send_request(url, headers, "POST", json_payload, True)

def create_loyalty_user_helper(payload):
    url = f'{proxyUrl}:5008/bank/loyalty/user/create'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session["access_token"]}'
    }

    json_payload = json.dumps(payload)

    return send_request(url, headers, "POST", json_payload, True)

def fetch_user_bank_transactions_helper(payload):
    url = f'{proxyUrl}:5005/bank/transaction/user/{payload["userId"]}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session["access_token"]}'
    }

    return send_request(url, headers, "GET", validate_token=True)

def fetch_user_bank_transaction_helper(payload):
    url = f'{proxyUrl}:5005/bank/transaction/{payload["refNum"]}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session["access_token"]}'
    }

    return send_request(url, headers, "GET", validate_token=True)

def delete_user_bank_transaction_helper(payload):
    url = f'{proxyUrl}:5005/bank/transaction/delete/{payload["refNum"]}'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session["access_token"]}'
    }

    return send_request(url, headers, "GET", validate_token=True)

def delete_ascenda_transaction_helper(payload):
    url = f'{ascendaUrl}:5004/ascenda/transaction/delete/{payload["refNum"]}'
    headers = {
        'Content-Type': 'application/json',
    }

    return send_request(url, headers, "GET")

def fetch_all_transactions_helper():
    url = f'{proxyUrl}:5005/bank/transaction'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {session["access_token"]}'
    }

    return send_request(url, headers, "GET", validate_token=True)

def validate_membership_helper(payload):
    url = f'{ascendaUrl}:5006/ascenda/loyalty/membership/{payload["loyalty_id"]}/{payload["member_id"]}'
    headers = {
        'Content-Type': 'application/json'
    }

    return send_request(url, headers, "GET")


def send_request(url, headers, method_type, payload = None, validate_token = False):
    if payload is None:
        resp = requests.request(method_type, url, headers=headers)
    else:
        resp = requests.request(method_type, url, headers=headers, data=payload)

    data = resp.json()
    res = {**data, "status": resp.status_code}

    return res

if __name__ == '__main__':
    # app.run(port=5000, host='0.0.0.0', debug=True)
    app.run(port=80, host='0.0.0.0', debug=True)


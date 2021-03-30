from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import requests, json
from os import environ

app = Flask(__name__, template_folder='./client/templates', static_folder='./client/static')
proxyUrl = environ.get('proxyUrl')
ascendaUrl = environ.get('ascendaUrl')
CORS(app)

@app.route("/")
def welcome_page():
    return render_template(
        'bank.html', 
        data = {
            'proxyUrl' : proxyUrl,
            'ascendaUrl' : ascendaUrl
        }
    )

@app.route("/transfer_summary")
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

    return render_template(
        'transfer_summary.html', 
        data = {
            'outcome_codes': outcome_codes,
            'proxyUrl' : proxyUrl,
            'ascendaUrl' : ascendaUrl
        },
    )

@app.route("/demo_polling")
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

    return render_template(
        'admin_transfer_summary.html', 
        data = {
            'outcome_codes': outcome_codes,
            'proxyUrl' : proxyUrl,
            'ascendaUrl' : ascendaUrl
        },
    )

@app.route("/loyalty_programme")
def loyalty_programme_page():

    resp = requests.get(f"{ascendaUrl}:5006/ascenda/loyalty")
    loyalties =  json.loads(resp.content)
    programs = []
    for item in loyalties["loyalty_programme"]:
        programs.append(item)

    resp = requests.get(f"{proxyUrl}:5008/bank/loyalty/user/" + request.cookies.get("userId"))
    memberships = json.loads(resp.content)

    user_membership = {}
    if "loyalty_user" in memberships:
        for item in memberships["loyalty_user"]:
            user_membership[item["loyalty_id"]] = item["member_id"]

    resp = requests.get(f"{proxyUrl}:5002/bank/user/" + request.cookies.get("userId"))
    user =  json.loads(resp.content)
    user = {
        "credits" : user["user"][0]["points"]
    }

    # featured_programs = [item for item in programs if item["isFeatured"]]

    data = {
        'programs' : programs,
        # 'featured_programs' : featured_programs,
        'user_membership' : user_membership,
        'user' : user,
        'proxyUrl' : proxyUrl,
        'ascendaUrl' : ascendaUrl
    }
    return render_template(
        'loyalty_programme.html', 
        data = data
    )

@app.route("/login")
def login_page():
    return render_template(
        'login.html', 
        data = {
            'proxyUrl' : proxyUrl
        }
    )

@app.route("/logout")
def logout_page():
    return render_template(
        'logout.html', 
    )

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0', debug=True)


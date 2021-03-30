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
import boto3
import boto
from csv_handler import *
from boto.s3.lifecycle import Lifecycle,Rule,Transition,Expiration

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/cs301_team1_ascenda'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://USERNAME:PASSWORD@ascenda-loyalty.canszqrplode.us-east-1.rds.amazonaws.com/cs301_team1_ascenda'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# TO-DO:
# Add a function that take in the reference_num and delete away all information from S3 bucket, S3 Glacier
# Include the link to S3 - the function should be able to download from S3 and upload to S3. 

access_key_id='AKIAS2IO6KUIKZBGACGP'
secret_access_key='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'

session = boto3.Session(
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
)

s3_client = session.client('s3')
s3_resource = session.resource('s3')
conn = boto.connect_s3(access_key_id, secret_access_key)

FOLDER = "handback/"

def checkBucketExist(bucket_name): 
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except:
        return False
    return True

def createBucket(bucket_name, region):
    if region == "us-east-1":
        s3_client.create_bucket(Bucket=bucket_name)
    else:
        s3_client.create_bucket(Bucket=bucket_name,
                                CreateBucketConfiguration={'LocationConstraint': region})

def blockAllPublicAccess(bucket_name):
    s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        },
    )

def setLifecyclePolicy(bucket_name):
    bucket = conn.get_bucket(bucket_name)
    bucket.configure_lifecycle(lifecycle)

lifecycle = Lifecycle()
transition = Transition(days=0, storage_class="GLACIER")
rule = Rule("movetoglacier", prefix="", status="Enabled", expiration=1825, transition=transition)
lifecycle.append(rule)

class AscendaTransaction(db.Model):
    __tablename__ = 'ascenda_file_name'

    reference_num = db.Column(db.String(120), primary_key=True)
    file_name = db.Column(db.String(120), primary_key=True)

    def __init__(self, reference_num, file_name):
        self.reference_num = reference_num
        self.file_name = file_name

    def json(self):
        return {"reference_num": self.reference_num, "file_name": self.file_name}

@app.route("/ascenda/filehandle/delete_bucket/<string:LoyaltyId>")
def delete_bucket(LoyaltyId):
    BUCKET = LoyaltyId.lower() + "-bucket-g1t1"
    if checkBucketExist(BUCKET) == True:
        bucket = s3_resource.Bucket(BUCKET)
        bucket.objects.all().delete()
        response_s3 = s3_client.delete_bucket(Bucket=BUCKET)
        response_db = requests.get('http://localhost:5006/ascenda/loyalty/delete/' + LoyaltyId)
        return jsonify({"message": "done"}), 201
    return jsonify({"message": "Bucket not found."}), 404

# send accrual to S3 buckets change filename to bank_timestamp
@app.route("/ascenda/filehandle/send_accrual/", methods=['POST'])
def send_accrual(*args, **kwargs):
    with app.app_context():
        try:
            partnercodes = requests.get('http://localhost:5004/ascenda/transaction/partner')
            partnercodes_data = partnercodes.json()

            today = datetime.now()
            for partnercode in partnercodes_data:
                transactions_for_partner = requests.get('http://localhost:5004/ascenda/transaction/partner/'+partnercode)
                transactions_for_partner_data = transactions_for_partner.json()
                transactions = transactions_for_partner_data["transaction"]
                if not not transactions:
                    transactions_dict = {}
                    for transaction in transactions:
                        if transaction['outcome_code'] == 0: 
                            key = transaction['loyalty_id']
                            if key in transactions_dict:
                                transactions_dict[key].append(transaction)
                            else:
                                transactions_dict[key] = [transaction]
                    for key, value in transactions_dict.items():
                        BUCKET = key.lower() + "-bucket-g1t1"

                        if checkBucketExist(BUCKET) == False:
                            createBucket(BUCKET, 'us-east-1')

                        blockAllPublicAccess(BUCKET)
                        setLifecyclePolicy(BUCKET)

                        file_name = partnercode + "_" + today.strftime("%Y%m%d_%H%M%S") + ".txt"
                        file_path = "../../accrual_file/" + file_name
                        bucket_file_path = "accrual/" + file_name
                        with open(file_path, mode="w", newline="") as accrual_file:
                            writer = csv.writer(accrual_file)
                            writer.writerow(["Index", "Member ID", "Member first name", "Member last name", "Transfer date", "Amount", "Reference number", "Partner code"])
                            for index, val in enumerate(value):
                                writer.writerow([index+1, val['member_id'], val['member_name_first'], val['member_name_last'], val['transaction_date'], val['amount'], val['reference_num'], val['partner_code']])
                                updateurl = 'http://localhost:5004/ascenda/transaction/update/'+ val['id'] + "/"
                                transaction_code = {'outcome_code': '1010'}
                                requests.post(updateurl, json = transaction_code)
                        s3_client.upload_file(file_path, BUCKET, bucket_file_path)
                        
            print ("done")
        except:
            print("error")
            return jsonify({"message": "An error occurred while processing the accrual"}), 500

        return jsonify({"message": "Success"}), 201

# process handback files from s3 buckets
@app.route("/ascenda/filehandle/process_handback/", methods=['POST'])
def process_handback():
    with app.app_context():
        try:
            response = requests.get('http://localhost:5006/ascenda/loyalty')
            response_data = response.json()
            loyalty_programs = response_data["loyalty_programme"]

            for loyalty_program in loyalty_programs:
                BUCKET = loyalty_program["loyalty_id"].lower() + "-bucket-g1t1"

                if checkBucketExist(BUCKET) == False:
                    continue
                paginator = s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=BUCKET, Prefix=FOLDER)

                for page in pages:
                    for obj in page['Contents']:
                        
                        handback = s3_client.get_object(Bucket=BUCKET, Key=obj.get('Key'))
                        partner_code = obj['Key'].split('/')[1].split('_')[0]
                        contents = handback['Body'].read().decode('utf-8')

                        # Facade Here
                        transactions = readCSVFromLoyalty(contents, loyalty_program["loyalty_id"])

                        # excution of transaction
                        for transaction in transactions:
                            if not not transaction:
                                geturl = 'http://localhost:5004/ascenda/transaction/partner/'+partner_code
                                reference_num = [transaction[2]]

                                transaction_for_partner = requests.get(geturl, json = reference_num)
                                transaction_for_partner_data = transaction_for_partner.json()
                                transactions_data = transaction_for_partner_data["transaction"]

                                for transaction_data in transactions_data:
                                    if transaction_data['outcome_code'] == 1010:
                                        updateurl = 'http://localhost:5004/ascenda/transaction/update/'+ transaction_data['id'] + "/"
                                        transaction_code = {'outcome_code': transaction[3]}
                                        requests.post(updateurl, json = transaction_code)
        except:
            print("error")
            return jsonify({"message": "An error occurred while processing the handback"}), 500
    return jsonify({"message": "Success"}), 201



    

app.scheduler = BackgroundScheduler()
app.scheduler.add_job(send_accrual, "cron", day_of_week='0-6', hour=20, minute=0)
app.scheduler.add_job(process_handback, "cron", day_of_week='0-6', hour=20, minute=10)
app.scheduler.start()

if __name__ == '__main__': # if it is the main program you run, then start flask
    # with docker
    app.run(host='0.0.0.0', port=5008, debug=True)
    # app.run(host='0.0.0.0', port=5008, debug=True, use_reloader=False) #to allow the file to be named other stuff apart from app.py
    # debug=True; shows the error and it will auto restart
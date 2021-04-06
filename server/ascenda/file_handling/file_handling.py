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
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:3306/cs301_team1_ascenda'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://admin:itsaadmin@ascenda-file-handling.cq4bzcmfnjpo.us-east-1.rds.amazonaws.com/cs301_team1_ascenda'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["dbURL"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


# TO-DO:
# Add a function that take in the reference_num and delete away all information from S3 bucket, S3 Glacier
# Include the link to S3 - the function should be able to download from S3 and upload to S3. 

class FileHandling(db.Model):
    __tablename__ = 'ascenda_file_name'

    reference_num = db.Column(db.String(120), primary_key=True) # to delete with
    partner_code = db.Column(db.String(120), nullable=False) # need it as we cant assume that bank_user_id is unique
    bank_user_id = db.Column(db.String(120), nullable=False) # to find reference_num associated with bank_user_id
    file_name = db.Column(db.String(120), primary_key=True) # to find file in bucket
    loyalty_id = db.Column(db.String(120), nullable=False) # to find bucket

    def __init__(self, reference_num, partner_code, bank_user_id, file_name, loyalty_id):
        self.reference_num = reference_num
        self.partner_code = partner_code
        self.bank_user_id = bank_user_id
        self.file_name = file_name
        self.loyalty_id = loyalty_id

    def json(self):
        return {"reference_num": self.reference_num, "partner_code": self.partner_code, "bank_user_id": self.bank_user_id, "file_name": self.file_name, "loyalty_id": self.loyalty_id}

# get all filehandle match
@app.route("/ascenda/filehandle")
def get_all_filehandle():
    # query for all transaction
	return jsonify({"filehandle": [filehandle.json() for filehandle in FileHandling.query.all()]})

# get filehandle details with Partner Code & Bank User ID
@app.route("/ascenda/filehandle/<string:PartnerCode>/<string:BankUserId>")
def find_by_bankUserId(PartnerCode, BankUserId):
    filehandle_info = FileHandling.query.filter_by(partner_code=PartnerCode,bank_user_id=BankUserId).all()
    if filehandle_info:
        return [filehandle.json() for filehandle in FileHandling.query.filter_by(partner_code=PartnerCode,bank_user_id=BankUserId)]
    return []

# create a new filehandle with details passed in 
def create_filehandle(ReferenceNum, PartnerCode, BankUserId, FileName, LoyaltyId):
    if (FileHandling.query.filter_by(reference_num=ReferenceNum, file_name=FileName).first()):
        return jsonify({"message": "The filehandle record already exists."}), 400

    filehandle_info = FileHandling(ReferenceNum, PartnerCode, BankUserId, FileName, LoyaltyId)
   
    try:
        db.session.add(filehandle_info)
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred creating the filehandle record."}), 500

    return jsonify(filehandle_info.json()), 201

# delete filehandle record
def delete_filehandle(PartnerCode, BankUserId):
    try:
        FileHandling.query.filter_by(partner_code=PartnerCode, bank_user_id=BankUserId).delete()
        db.session.commit()
        
    except:
        return jsonify({"message": "An error occurred deleting the records."}),500

    return jsonify({"message": "Filehandle records deleted successfully"}), 201


#-----------------------------------------------------------------------------------------------------------------------
# connection to s3
access_key_id='AKIA2OKFRCBLVW5I3KVT'
secret_access_key='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'

session = boto3.Session(
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
)

s3_client = session.client('s3')
s3_resource = session.resource('s3')
s3_transfer = boto3.client('transfer')
conn = boto.connect_s3(access_key_id, secret_access_key)

# Constants
FOLDER = "handback/"
paginator = s3_client.get_paginator('list_objects_v2')

# Functions for filehandling
def checkFolderExist(bucket_name, folder): 
    bucket = s3_resource.Bucket(bucket_name)
    objs = list(bucket.objects.filter(Prefix=folder))
    if(len(objs)>0):
        return True
    return False

def deleteFromFolder(bucket_name, folder, partner_code):
    pages = paginator.paginate(Bucket=bucket_name, Prefix=folder)
    for page in pages:
        for obj in page['Contents']:
            partnerCode = obj['Key'].split('/')[1].split('_')[0]
            if partnerCode == partner_code:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])

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

def setEncryption(bucket_name):
    s3_client.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
          'Rules': [
            {
                'ApplyServerSideEncryptionByDefault': {
                    'SSEAlgorithm': 'AES256'
                }
            },
          ]
        }
    )

def createUserForTransfer(bucket_name, loyalty):
    home = f'/' + bucket_name + ''
    username = loyalty.lower() + "-user"
    s3_transfer.create_user(
        HomeDirectory=home,
        Role='arn:aws:iam::717942231127:role/RoleForTransferFamily',
        ServerId='s-05f2939e78c143f99',
        SshPublicKeyBody='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCi7q2heVGZCELE/A17BdWjwK7yDQVFBNPK96t36lW76Ug4Un3VE49Pez/bspo4pR95orSZbeGdb/SncuI3X8WUNgVoM6lnc3YwD+mmxkWaqlSBhpA/fpucrhg7YXMjSfGvo0xgywpjHV3JCXsF+fQsY3Jj3R9YowChRoaRMwDU2Aj2hZTu4qx6PifORe2TxKDG2nNcwiYuO5x2dOqZlozCXUMwKgEknBl+kXgav4XRDILmv9rI5mbkOmeXmYcnZTB7pY4h/LPmKHVyQaIgd9h3npvqFejONOxcW2qOvDm2fA/T2NALJligKzJaQLj2jvOapWuUKd1Iq0WYymTd/pm9 fionaweeee@LAPTOP-4A9RVO9N',
        UserName=username
    )

def deleteUserForTransfer(bucket_name, loyalty):
    username = loyalty.lower() + "-user"
    s3_transfer.delete_user(
        ServerId='s-05f2939e78c143f99',
        UserName=username
    )

def restoreFile(bucket_name, file_name):
    s3_client.restore_object(
        Bucket=bucket_name, 
        Key=file_name,
        RestoreRequest={'Days': 1, 'GlacierJobParameters': {'Tier': 'Standard'}})

# create rule for lifecycle, set None for expiration for now
lifecycle = Lifecycle()
transition = Transition(days=0, storage_class="GLACIER")
rule = Rule("movetoglacier", prefix="", status="Enabled", expiration=None, transition=transition)
lifecycle.append(rule)

#-----------------------------------------------------------------------------------------------------------------------

@app.route("/ascenda/filehandle/health_check")
def health_check():
    return jsonify({"message": "Success"}), 200

@app.route("/ascenda/filehandle/delete_loyalty/<string:LoyaltyId>")
def delete_loyalty(LoyaltyId):
    BUCKET = LoyaltyId.lower() + "-bucket-g1t1"
    try:
        if checkBucketExist(BUCKET) == True:
            bucket = s3_resource.Bucket(BUCKET)
            bucket.objects.all().delete()
            #deleteUserForTransfer(BUCKET, LoyaltyId)
            response_s3 = s3_client.delete_bucket(Bucket=BUCKET)
    except:
        return jsonify({"message": "An error occurred while processing the accrual"}), 500
    return jsonify({"message": "Success"}), 201


@app.route("/ascenda/filehandle/delete_bank/<string:PartnerCode>")
def delete_bank(PartnerCode):
    response = requests.get('http://ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:5006/ascenda/loyalty')
    response_data = response.json()
    loyalty_programs = response_data["loyalty_programme"]

    for loyalty_program in loyalty_programs:
        BUCKET = loyalty_program["loyalty_id"].lower() + "-bucket-g1t1"
        if checkBucketExist(BUCKET) == False:
            continue
        if checkFolderExist(BUCKET, "accrual/"):
            deleteFromFolder(BUCKET, "accrual/", PartnerCode)
        if checkFolderExist(BUCKET, "handback/"):
            deleteFromFolder(BUCKET, "handback/", PartnerCode)
        if checkFolderExist(BUCKET, "processed/"):
            deleteFromFolder(BUCKET, "processed/", PartnerCode)
        return jsonify({"message": "Success"}), 201
    return jsonify({"message": "An error occurred while deleting the accrual"}), 500

@app.route("/ascenda/filehandle/delete_user/<string:PartnerCode>/<string:BankUserId>")
def delete_user(PartnerCode, BankUserId):
    try:
        response = find_by_bankUserId(PartnerCode, BankUserId)
        storageClasses = list()

        for record in response:
            BUCKET = record['loyalty_id'].lower() + "-bucket-g1t1"
            print(record['file_name'])
            key = s3_resource.Object(BUCKET, record['file_name'])
            if (key.storage_class == "GLACIER"):
                storageClasses.append("GLACIER")
                restoreFile(BUCKET, record['file_name'])
                print("Data deleted from database, deletion of files will be processed in 6 hours time")
        
        if "GLACIER" in storageClasses:
            time.sleep(21600)
            
        for record in response:
            BUCKET = record['loyalty_id'].lower() + "-bucket-g1t1"
            folder = record['file_name'].split('/')[0]
            fileToEdit = s3_client.get_object(Bucket=BUCKET, Key=record['file_name'])
            data = fileToEdit['Body'].read().decode('utf-8')
            index = 6
            headers, transactions = readCSVFromLoyalty(data, "DEFAULT")
            if folder == "handback":
                headers, transactions = readCSVFromLoyalty(data, record['loyalty_id'])
                index = 2
                
            clean_transactions = [transaction for transaction in transactions if transaction != []]
            if len(list(clean_transactions)) == 1:
                s3_client.delete_object(Bucket=BUCKET, Key=record['file_name'])
            else:
                lines = list()
                lines.append(headers)

                for transaction in clean_transactions:
                    if transaction[index] == record['reference_num']:
                        lines.append(transaction)

                if len(lines) <= 1:
                    s3_client.delete_object(Bucket=BUCKET, Key=record['file_name'])
                else:
                    writer_buffer = io.StringIO()
                    writer = csv.writer(writer_buffer)
                    writer.writerows(lines)
                    buffer_to_upload = io.BytesIO(writer_buffer.getvalue().encode())
                    s3_client.put_object(Body=buffer_to_upload, Bucket=BUCKET, Key=record['file_name'])
        delete_filehandle(PartnerCode, BankUserId)
    except:
        print("error")
        return jsonify({"message": "An error occurred while processing the handback"}), 500
    return jsonify({"message": "Success"}), 201


# send accrual to S3 buckets change filename to bank_timestamp
@app.route("/ascenda/filehandle/send_accrual/", methods=['POST'])
def send_accrual(*args, **kwargs):
    with app.app_context():
        try:
            partnercodes = requests.get('http://ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:5004/ascenda/transaction/partner')
            partnercodes_data = partnercodes.json()
            
            today = datetime.now()
            for partnercode in partnercodes_data:
                transactions_for_partner = requests.get('http://ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:5004/ascenda/transaction/partner/'+partnercode)
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
                            createBucket(BUCKET, 'ap-southeast-1')
                            blockAllPublicAccess(BUCKET)
                            setLifecyclePolicy(BUCKET)
                            setEncryption(BUCKET)
                            #createUserForTransfer(BUCKET, key)

                        file_name = partnercode + "_" + today.strftime("%Y%m%d_%H%M%S") + ".txt"
                        file_path = "../../../files/" + file_name
                        bucket_file_path = "accrual/" + file_name
                        with open(file_path, mode="w", newline="") as accrual_file:
                            writer = csv.writer(accrual_file)
                            writer.writerow(["Index", "Member ID", "Member first name", "Member last name", "Transfer date", "Amount", "Reference number", "Partner code"])
                            for index, val in enumerate(value):
                                writer.writerow([index+1, val['member_id'], val['member_name_first'], val['member_name_last'], val['transaction_date'], val['amount'], val['reference_num'], val['partner_code']])
                                updateurl = 'http://ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:5004/ascenda/transaction/update/'+ val['reference_num'] + "/"
                                transaction_code = {'outcome_code': '1010'}
                                requests.post(updateurl, json = transaction_code)
                                create_filehandle(val['reference_num'], partnercode, val['bank_user_id'], bucket_file_path, key)
                        s3_client.upload_file(file_path, BUCKET, bucket_file_path)
                        
            print ("done")
        except requests.exceptions.RequestException as e:
            print("error")
            print(e)
            return jsonify({"message": "An error occurred while processing the accrual"}), 500

        return jsonify({"message": "Success"}), 201

# process handback files from s3 buckets
@app.route("/ascenda/filehandle/process_handback/", methods=['POST'])
def process_handback():
    with app.app_context():
        try:
            response = requests.get('http://ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:5006/ascenda/loyalty')
            response_data = response.json()
            loyalty_programs = response_data["loyalty_programme"]

            for loyalty_program in loyalty_programs:
                BUCKET = loyalty_program["loyalty_id"].lower() + "-bucket-g1t1"

                if checkBucketExist(BUCKET) == False:
                    continue
                if checkFolderExist(BUCKET, FOLDER) == False:
                    continue
                pages = paginator.paginate(Bucket=BUCKET, Prefix=FOLDER)

                for page in pages:
                    for obj in page['Contents']:
                        
                        handback = s3_client.get_object(Bucket=BUCKET, Key=obj.get('Key'))
                        
                        file_name = obj['Key'].split('/')[1]
                        new_path = 'processed/' + file_name
                        partner_code = file_name.split('_')[0]
                        contents = handback['Body'].read().decode('utf-8')

                        # Facade Here
                        headers, transactions = readCSVFromLoyalty(contents, loyalty_program["loyalty_id"])

                        # excution of transaction
                        for transaction in transactions:
                            if not not transaction:
                                geturl = 'http://ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:5004/ascenda/transaction/partner/'+partner_code
                                reference_num = [transaction[2]]

                                transaction_for_partner = requests.get(geturl, json = reference_num)
                                transaction_for_partner_data = transaction_for_partner.json()
                                transactions_data = transaction_for_partner_data["transaction"]

                                for transaction_data in transactions_data:
                                    if transaction_data['outcome_code'] == 1010:
                                        updateurl = 'http://ascenda-load-balancer-1751800571.us-east-1.elb.amazonaws.com:5004/ascenda/transaction/update/'+ transaction_data['reference_num'] + "/"
                                        transaction_code = {'outcome_code': transaction[3]}
                                        requests.post(updateurl, json = transaction_code)
                                        #create_filehandle(transaction_data['reference_num'], transaction_data['partner_code'], transaction_data['bank_user_id'], new_path, loyalty_program)
                        copy_source = { 'Bucket': BUCKET, 'Key': obj['Key'] }
                        s3_resource.meta.client.copy(copy_source, BUCKET, new_path)
                        s3_client.delete_object( Bucket=BUCKET, Key=obj['Key'], )
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
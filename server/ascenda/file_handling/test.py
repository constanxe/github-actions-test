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
from boto.s3.lifecycle import Lifecycle,Rule,Transition,Expiration

access_key_id='AKIAS2IO6KUIKZBGACGP'
secret_access_key='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'

session = boto3.Session(
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
)

# BUCKET = "tests34transfer"
FOLDER = "handback/"
s3_client = session.client('s3')

lifecycle = Lifecycle()
transition = Transition(days=0, storage_class="GLACIER")
rule = Rule("movetoglacier", prefix="", status="Enabled", expiration=1825, transition=transition)
lifecycle.append(rule)

bucket_name = "testingquantum-bucket-g1t1"
bucket = s3_client.create_bucket(Bucket=bucket_name)

response_public = s3_client.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            'BlockPublicAcls': True,
            'IgnorePublicAcls': True,
            'BlockPublicPolicy': True,
            'RestrictPublicBuckets': True
        },
    )

conn = boto.connect_s3(access_key_id, secret_access_key)
bucket = conn.get_bucket(bucket_name) 
bucket.configure_lifecycle(lifecycle)

# response = s3_client.delete_bucket(Bucket=bucket_name)
# print(response)

# paginator = s3_client.get_paginator('list_objects_v2')
# pages = paginator.paginate(Bucket=BUCKET, Prefix=FOLDER)

# for page in pages:
#     for obj in page['Contents']:
#         handback = s3_client.get_object(Bucket=BUCKET, Key=obj.get('Key'))
#         partner_code = obj['Key'].split('/')[1].split('_')[0]
#         contents = handback['Body'].read().decode('utf-8')
#         reader = csv.reader(contents.split('\r\n'))
#         transactions = []
#         header = next(reader)
#         for row in reader:
#             transactions.append(row)
#         for transaction in transactions:
#             if not not transaction:
#                 print(transaction)

#s3_client.upload_file("../../accrual_file/EMINENT_20210327_021058.txt", BUCKET, "accrual/EMINENT_20210327_021058.txt")
#s3_resource.meta.client.upload_file(Filename="../../accrual_file/QUANTUM_20210327_013444.txt", Bucket=BUCKET, Key="accrual/test.txt")
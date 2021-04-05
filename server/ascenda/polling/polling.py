from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
import os
import json
import base64
import uuid
import amazondax
import botocore.session

app = Flask(__name__)
CORS(app)

my_session = boto3.session.Session()

region = 'us-east-1'
dynamodb = boto3.resource('dynamodb', region_name=region)
tablename = 'polling'
session = botocore.session.get_session()
dax_endpoint = "polling-1-cluster.evzyxg.clustercfg.dax.use1.cache.amazonaws.com:8111"
dax_client = amazondax.AmazonDaxClient(session, region_name=region, endpoints=[dax_endpoint])

@app.route("/polling/healthcheck", methods=["GET"])
def heartbeat():
    return jsonify({"message": "Success"}), 200
    
@app.route("/polling/<string:reference_num>", methods=['GET'])
def get_transaction(reference_num):
    #To get transaction status
    try:
        # DAX cluster
        # Remember to add IAM policy to the role which the service is being called from
        params = {
            'TableName' : tablename,
            "Key":{
                'reference_num': {"S": reference_num}
            }
        }

        response = dax_client.get_item(**params)
        #  End of DAX cluster

        transaction = response['Item']
    except Exception as e:
        # return jsonify({"message": "Transaction not found."}), 404
        return jsonify({"message": str(e)}), 404
    
    # return transaction
    return jsonify(transaction)
    
@app.route("/polling/accrual", methods=['POST'])
def accrual():
    data = request.get_json()
    try:
        dynamodb.Table(tablename).put_item(
            Item={
                'reference_num': data['reference_num'],
                'partner_code': data['partner_code'],
                'loyalty_id': data['loyalty_id'],
                'outcome_code': 0
            }
        )
    except Exception as e:
        return jsonify({'message': "Failed to update Dynamo"}), 500
        
    return jsonify({"message": "Successfully added transaction"}), 201

@app.route("/polling/update/<string:reference_num>/<string:status_code>", methods=["PUT"])
def update_transaction(reference_num, status_code):
    print(status_code)
    try:
        # DAX cluster
        # Remember to add IAM policy to the role which the service is being called from
        params = {
            'TableName' : tablename,
            "Key":{
                'reference_num': {"S": reference_num}
            }
        }

        response = dax_client.get_item(**params)
        #  End of DAX cluster

        transaction_exist = bool(response['Item'])
        
        if not transaction_exist:
            return jsonify({"message": "Transaction not found"})
        else:
            dynamodb.Table(tablename).update_item(
                Key={
                    'reference_num': reference_num
                },
                UpdateExpression = 'SET #outcome_code  = :val',
                ExpressionAttributeValues={
                    ':val': status_code
                },
                ExpressionAttributeNames={
                    '#outcome_code': 'outcome_code'
                }
            )
            
    except Exception as e:
        print(e)
        return jsonify({"message": str(e)}), 404
    return "Successfully updated", 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5009, debug=True)
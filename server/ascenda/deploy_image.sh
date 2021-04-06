#!/bin/bash

export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AVAIL_ZONE=`curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone`
export REGION="`echo \"$AVAIL_ZONE\" | sed 's/[a-z]$//'`"

aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

docker build -t loyalty:1.0.0 ./loyalty/
docker build -t exchange_rate:1.0.0 ./exchange_rate/
docker build -t file_handling:1.0.0 ./file_handling/
docker build -t transaction:1.0.0 ./transaction/
docker build -t polling:1.0.0 ./polling/

docker tag loyalty:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/loyalty:1.0.0
docker tag exchange_rate:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/exchange_rate:1.0.0
docker tag file_handling:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/file_handling:1.0.0
docker tag transaction:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/transaction:1.0.0
docker tag polling:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/polling:1.0.0

docker tag ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/loyalty:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/loyalty:latest
docker tag ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/exchange_rate:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/exchange_rate:latest
docker tag ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/file_handling:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/file_handling:latest
docker tag ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/transaction:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/transaction:latest
docker tag ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/polling:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/polling:latest

docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/loyalty:1.0.0
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/exchange_rate:1.0.0
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/file_handling:1.0.0
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/transaction:1.0.0
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/polling:1.0.0

docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/loyalty:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/exchange_rate:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/file_handling:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/transaction:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/polling:latest
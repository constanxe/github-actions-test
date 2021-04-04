#!/bin/bash

export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AVAIL_ZONE=`curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone`
export REGION="`echo \"$AVAIL_ZONE\" | sed 's/[a-z]$//'`"

aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

docker build -t loyalty:1.0.0 ./loyalty/

docker tag loyalty:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/loyalty:1.0.0

docker tag ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/loyalty:1.0.0 ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/loyalty:latest

docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/loyalty:1.0.0

docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/loyalty:latest
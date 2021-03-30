
aws ecr create-repository --repository-name ascenda-test --image-scanning-configuration scanOnPush=true --region us-east-1

aws ecs register-task-definition --region us-east-1 --cli-input-json file://$HOME/Desktop/ascenda-test/ascenda-test/task-def.json

aws ecs create-cluster --region us-east-1 --cluster-name default

aws ecs create-service --region us-east-1 --service-name fargate-service --task-definition sample-fargate:1 --desired-count 2 --launch-type "FARGATE" --network-configuration "awsvpcConfiguration={subnets=[subnet-011126a15d4118ab2],securityGroups=[sg-04ceaf462b4dbd50c]}"


git remote add origin git@github.com:constanxe/ascenda-test.git
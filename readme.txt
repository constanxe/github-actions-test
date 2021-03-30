aws ecs describe-task-definition \
   --task-definition loyalty \
   --query taskDefinition > task-definition.json

aws ecs register-task-definition \
   --generate-cli-skeleton > task-definition.json
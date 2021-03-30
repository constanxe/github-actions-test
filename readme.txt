aws ecs describe-task-definition --task-definition loyalty --query taskDefinition > loyalty-task-definition.json

aws ecs describe-task-definition --task-definition exchange_rate --query taskDefinition > exchange-task-definition.json

aws ecs describe-task-definition --task-definition transaction --query taskDefinition > transaction-task-definition.json
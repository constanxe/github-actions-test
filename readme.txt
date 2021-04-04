aws ecs describe-task-definition --task-definition file_handling --query taskDefinition > task-definitions/file_handling-taskdef.json
aws ecs describe-task-definition --task-definition bank --query taskDefinition > task-definitions/bank-taskdef.json
aws ecs describe-task-definition --task-definition loyalty --query taskDefinition > task-definitions/loyalty-taskdef.json
aws ecs describe-task-definition --task-definition polling-task --query taskDefinition > task-definitions/polling-taskdef.json
aws ecs describe-task-definition --task-definition transaction --query taskDefinition > task-definitions/transaction-taskdef.json

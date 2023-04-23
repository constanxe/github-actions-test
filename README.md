## GitHub Actions

**Continuous integration and continuous development (CI/CD)** was done with GitHub Actions. When a push or pull request is made to the branches and paths we are watching, the workflow is triggered and it:

1. **Deploys** the containerised workloads to AWS Fargate
 - Build, tag with Github SHA and push new Docker container image to Amazon ECR
 - Update task definition with the latest tagged image
 - Deploy the new task definition to Amazon ECS
2. Runs automated **tests** on all the deployed APIs
 - Includes APIs for services which were not identified for that workflow
 - Acts as regression testing to ensure bugs are not introduced to other services and previously working code
 - Health checks and assertions on the GET responses are performed to ensure that the deployment was successful

Extra measures we took to **streamline** the CI/CD process to save resources are as follows.
- **Concurrent running of jobs**: if multiple services are identified, allows all workflow jobs to be ran in parallel, which otherwise may not be possible if some are stopped due to errors
- **Path changes filter**: identifies where the code was modified, allowing conditional execution of workflow jobs (e.g. deployment) only for the changed components
- **Cancel outdated workflow runs**: only the most recent workflow will run at any time
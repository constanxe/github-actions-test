# CS301 IT Solution Architecture

## GitHub Actions

You may refer to the following for the Continuous Integration and Continuous Development (CI/CD) process.
- Workflow: [.github/workflows/aws.yml](https://github.com/constanxe/github-actions-test/blob/main/.github/workflows/aws.yml)
- Example of a workflow run: [CI/CD which showcased streamlining via 'Concurrent running of jobs' and 'Path changes filter'](https://github.com/constanxe/github-actions-test/actions/runs/719363493)

Take note that this was solely a temporary space for testing the workflow, hence every other code is outdated and was contributed by my group too.


### Explanation

When a push or pull request is made to the branches and paths we are watching, the workflow is triggered and it:

1. **Deploys** the containerised workloads to AWS Fargate
	1. Build, tag with Github SHA and push new Docker container image to Amazon ECR
	2. Update task definition with the latest tagged image
	3. Deploy the new task definition to Amazon ECS
2. Runs automated **tests** on all the deployed APIs
	1. Includes APIs for services which were not identified for that workflow
	2. Acts as regression testing to ensure bugs are not introduced to other services and previously working code
	3. Health checks and assertions on the GET responses are performed to ensure that the deployment was successful

Extra measures we took to **streamline** the CI/CD process to save resources are as follows.
- **Concurrent running of jobs**: if multiple services are identified, allows all workflow jobs to be ran in parallel, which otherwise may not be possible if some are stopped due to errors
- **Path changes filter**: identifies where the code was modified, allowing conditional execution of workflow jobs (e.g. deployment) only for the changed components
- **Cancel outdated workflow runs**: only the most recent workflow will run at any time

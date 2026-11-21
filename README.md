# Deploy to AWS ECS Fargate with GitHub Actions (no access keys)

A small Python web app that goes live on **AWS ECS Fargate** behind an **Application Load Balancer**.
Every `git push` to `main` builds a new image, pushes it to **ECR** and deploys it with **GitHub Actions**.
GitHub logs in to AWS with **OIDC** (short-lived credentials), so there are **no AWS access keys** in this repo or in GitHub secrets.

Video walkthrough: StackFix Pro on YouTube (@stackfixpro).

```
git push -> GitHub Actions -> (OIDC, no keys) -> ECR -> ECS Fargate (2 tasks) -> ALB -> browser
```

## What is in this repo

| File | What it does |
|---|---|
| `app.py` | Flask app: `/` shows the version and which task answered, `/health` is the load balancer's health check |
| `Dockerfile` | Python 3.13 slim image, runs as a non-root user, listens on port 8080 |
| `.github/workflows/deploy.yml` | Build -> push to ECR -> new task definition -> deploy to ECS -> wait until stable |
| `aws/github-deploy-policy.json` | The only permissions GitHub gets (one ECR repo, one ECS service) |
| `aws/github-trust-policy.json` | Who may use the role: only this repo's `main` branch |

## Names used everywhere

| Thing | Name |
|---|---|
| Region | `ap-southeast-2` (Asia Pacific, Sydney). Using another Region? Change it in `deploy.yml` and `aws/github-deploy-policy.json`. |
| VPC | `stackfix-vpc` (10.0.0.0/16, 2 public subnets, no NAT Gateway) |
| Security groups | `alb-sg` (port 80 from the internet), `app-sg` (port 8080 only from `alb-sg`) |
| ECR repository | `stackfix-app` |
| Target group / load balancer | `stackfix-tg` (IP targets, HTTP 8080, health check `/health`) / `stackfix-alb` |
| ECS cluster / task definition / service | `stackfix-cluster` / `stackfix-task` (container `app`, 0.25 vCPU, 0.5 GB) / `stackfix-service` (2 tasks) |
| IAM role for GitHub | `github-actions-deploy` with policy `github-deploy-ecs` |

## Steps (short version)

1. **Network:** create `stackfix-vpc` with "VPC and more" (2 AZs, 2 public subnets, 0 private, NAT Gateway: None),
   then the two security groups.
2. **ECR:** create `stackfix-app`. Push the first image from AWS CloudShell with the repository's "View push commands".
3. **Load balancer:** target group `stackfix-tg` (type IP, port 8080, health check `/health`, no targets),
   then the ALB `stackfix-alb` (internet-facing, both public subnets, `alb-sg`, listener HTTP 80 -> `stackfix-tg`).
4. **ECS:** cluster `stackfix-cluster` (Fargate), task definition `stackfix-task` (image `...stackfix-app:latest`,
   port 8080), service `stackfix-service` (2 tasks, public subnets, **public IP ON**, `app-sg`, existing ALB + target group,
   circuit breaker with rollback). Open the ALB's DNS name.
5. **OIDC:** IAM -> Identity providers -> OpenID Connect: `https://token.actions.githubusercontent.com`, audience
   `sts.amazonaws.com`. Create policy `github-deploy-ecs` from `aws/github-deploy-policy.json` (replace `ACCOUNT_ID`),
   then role `github-actions-deploy` (Web identity, your GitHub user, this repo, branch `main`).
6. **GitHub:** Settings -> Secrets and variables -> Actions -> **Variables** -> `AWS_ROLE_ARN` = the role's ARN.
   Add `.github/workflows/deploy.yml`. Change `VERSION` in `app.py` and push: the new version is live a few minutes later.

> Learning setup: the tasks sit in public subnets with a public IP so they can pull from ECR without a NAT Gateway.
> Only the load balancer can reach them (`app-sg`). In production, put tasks in private subnets with a NAT Gateway
> or VPC endpoints.

## Delete everything (stop the cost)

Delete in this order: ECS service -> ECS cluster -> load balancer -> target group -> ECR repository ->
security groups `app-sg` and `alb-sg` -> VPC `stackfix-vpc` -> CloudWatch log group `/ecs/stackfix-task`.
The IAM role, policy and OIDC provider cost nothing (delete them too if you are done).

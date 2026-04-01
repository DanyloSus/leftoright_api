# Deployment Guide — EC2 + RDS + ElastiCache

## Architecture

- **EC2**: Runs the FastAPI app as a Docker container behind Nginx
- **RDS (PostgreSQL 16)**: Managed database replacing the local Postgres container
- **ElastiCache (Redis)**: Managed Redis replacing the local Redis container

## Prerequisites

### AWS Resources

1. **ECR Repository** — create one named `leftoright/prod`:
   ```bash
   aws ecr create-repository --repository-name leftoright/prod --region <region>
   ```

2. **RDS PostgreSQL instance** — ensure the security group allows inbound from the EC2 security group on port 5432.

3. **ElastiCache Redis cluster** — ensure the security group allows inbound from the EC2 security group on port 6379.

4. **EC2 instance** (Ubuntu 22.04+) — open ports 80 (HTTP), 443 (HTTPS), and 22 (SSH).

> All three resources must be in the same VPC / reachable subnets.

### GitHub Secrets

Add these in **Settings → Secrets and variables → Actions**:

| Secret              | Description                                         |
|---------------------|-----------------------------------------------------|
| `AWS_ACCESS_KEY_ID` | IAM user with ECR push + EC2 permissions             |
| `AWS_SECRET_ACCESS_KEY` | Corresponding secret key                        |
| `EC2_HOST`          | Public IP or hostname of the EC2 instance            |
| `EC2_USER`          | SSH user (`ubuntu` for Ubuntu AMIs)                  |
| `EC2_SSH_KEY`       | Private SSH key (PEM format) for the EC2 instance    |

Optionally set the **repository variable** `AWS_REGION` (defaults to `eu-north-1`).

## Initial EC2 Setup (one-time)

```bash
# SSH into the instance
ssh -i key.pem ubuntu@<ec2-host>

# Upload and run the setup script
sudo bash setup-ec2.sh

# Configure Nginx
sudo cp /home/ubuntu/app/nginx.conf /etc/nginx/sites-available/api
sudo ln -sf /etc/nginx/sites-available/api /etc/nginx/sites-enabled/api
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Configure AWS CLI for ECR pulls
aws configure  # enter credentials with ecr:GetAuthorizationToken + ecr:BatchGetImage

# Create production env file
cp /home/ubuntu/app/.env.prod.example /home/ubuntu/app/.env.prod
nano /home/ubuntu/app/.env.prod  # fill in RDS, ElastiCache, JWT, CORS values
```

## How Deployment Works

On every push to `main`/`master`:

1. **Lint** — `ruff check` & `ruff format --check`
2. **Test** — runs `pytest -v` with SQLite in-memory
3. **Deploy** (only after lint + test pass):
   - Builds Docker image and pushes to ECR (tagged with commit SHA + `latest`)
   - SCPs deploy files to EC2
   - SSHs into EC2 and runs `deploy.sh` which:
     - Logs into ECR
     - Pulls the new image
     - Runs Alembic migrations
     - Restarts the app container
     - Prunes old images

## File Layout

```
deploy/
├── .env.prod.example       # Template for production env vars
├── deploy.sh               # Runs on EC2 during each deployment
├── docker-compose.prod.yml # Production compose (no DB/Redis containers)
├── nginx.conf              # Nginx reverse proxy config
└── setup-ec2.sh            # One-time EC2 setup
```

## Manual Deployment

If you need to deploy manually:

```bash
ssh -i key.pem ubuntu@<ec2-host>

cd /home/ubuntu/app
ECR_REGISTRY=<account-id>.dkr.ecr.<region>.amazonaws.com
ECR_REPOSITORY=leftoright/prod
IMAGE_TAG=latest
AWS_REGION=<region>

bash deploy.sh "$ECR_REGISTRY" "$ECR_REPOSITORY" "$IMAGE_TAG" "$AWS_REGION"
```

## Rollback

Deploy a previous image tag:

```bash
ssh -i key.pem ubuntu@<ec2-host>
cd /home/ubuntu/app
bash deploy.sh <ecr-registry> leftoright/prod <previous-commit-sha> <region>
```

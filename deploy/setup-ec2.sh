#!/usr/bin/env bash
# One-time EC2 instance setup script.
# Run as root or with sudo on a fresh Ubuntu 22.04+ AMI.
set -euo pipefail

echo "==> Installing Docker"
apt-get update
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "==> Installing Nginx"
apt-get install -y nginx

echo "==> Installing AWS CLI"
apt-get install -y unzip
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -qo /tmp/awscliv2.zip -d /tmp
/tmp/aws/install --update
rm -rf /tmp/aws /tmp/awscliv2.zip

echo "==> Adding ubuntu user to docker group"
usermod -aG docker ubuntu

echo "==> Creating app directory"
mkdir -p /home/ubuntu/app
chown ubuntu:ubuntu /home/ubuntu/app

echo "==> Setup complete. Next steps:"
echo "  1. Copy deploy/nginx.conf to /etc/nginx/sites-available/api"
echo "  2. ln -sf /etc/nginx/sites-available/api /etc/nginx/sites-enabled/api"
echo "  3. rm -f /etc/nginx/sites-enabled/default"
echo "  4. systemctl reload nginx"
echo "  5. Configure AWS credentials: aws configure"
echo "  6. Place .env.prod in /home/ubuntu/app/"

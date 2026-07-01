---
title: Self-Hosted
sort: 130
section-id: deployment
keywords: self-hosted, VPS, nginx, PM2, systemd, Linux, server deployment
description: Running Velox on a VPS with nginx as a reverse proxy, managed by PM2 or systemd
language: en
---

# Self-Hosted

Deploying Velox to your own server (a VPS, dedicated server, or on-premises machine) gives you full control over your infrastructure. This guide covers setting up a Linux server with nginx as a reverse proxy, and managing the Node.js process with either PM2 or systemd.

## Server Preparation

This guide assumes Ubuntu 24.04 LTS. Adjust package manager commands for other distributions.

```bash
# Update the system
sudo apt update && sudo apt upgrade -y

# Install Node.js (LTS) via nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
source ~/.bashrc
nvm install 22
nvm use 22
nvm alias default 22

# Install nginx
sudo apt install -y nginx

# Install PostgreSQL (if needed)
sudo apt install -y postgresql postgresql-contrib

# Install Redis (if needed)
sudo apt install -y redis-server
```

## Deploying the Application

### Option A: Direct File Copy

```bash
# On your local machine — build the app
npm run build

# Copy build output to the server
rsync -avz --delete .velox/output/ user@your-server.com:/var/www/my-velox-app/
rsync -avz package.json package-lock.json user@your-server.com:/var/www/my-velox-app/

# On the server — install production dependencies
cd /var/www/my-velox-app
npm ci --omit=dev
```

### Option B: Git + CI/CD

Create a deploy script on the server:

```bash
#!/bin/bash
# /home/deploy/deploy.sh
set -e

APP_DIR=/var/www/my-velox-app
REPO=https://github.com/your-org/your-repo.git

cd $APP_DIR

# Pull latest code
git fetch --all
git reset --hard origin/main

# Install dependencies
npm ci --frozen-lockfile --omit=dev

# Build
npm run build

# Restart application
pm2 reload my-velox-app --update-env

echo "Deployment complete."
```

Call this from your GitHub Actions workflow:

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: deploy
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: /home/deploy/deploy.sh
```

## Environment Variables

Store production secrets in `/etc/environment` or a `.env.production` file:

```bash
# /etc/environment (system-wide)
NODE_ENV=production
DATABASE_URL=postgresql://velox:secretpass@localhost:5432/velox
SESSION_SECRET=your-long-random-secret-here
JWT_SECRET=another-long-random-secret

# Or in a project-specific .env.production
sudo nano /var/www/my-velox-app/.env.production
```

Load the env file in your start command (covered below).

## Process Management with PM2

PM2 is a battle-tested process manager for Node.js applications.

```bash
npm install -g pm2
```

Create a PM2 ecosystem file:

```javascript
// /var/www/my-velox-app/ecosystem.config.js
module.exports = {
  apps: [{
    name: 'my-velox-app',
    script: 'server.js',
    cwd: '/var/www/my-velox-app',
    instances: 'max',           // one process per CPU core
    exec_mode: 'cluster',       // enable cluster mode for zero-downtime restarts
    env_file: '/var/www/my-velox-app/.env.production',
    env: {
      NODE_ENV: 'production',
      PORT: 3700,
    },
    error_file: '/var/log/pm2/my-velox-app-error.log',
    out_file: '/var/log/pm2/my-velox-app-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
    max_memory_restart: '500M', // restart if memory exceeds 500 MB
  }],
};
```

Start and persist:

```bash
pm2 start ecosystem.config.js
pm2 save             # persist process list across reboots
pm2 startup          # install systemd startup script

# Useful commands
pm2 status
pm2 logs my-velox-app
pm2 reload my-velox-app    # zero-downtime reload
pm2 restart my-velox-app   # full restart
pm2 monit                  # real-time monitoring
```

## systemd Service (Alternative to PM2)

For simpler setups, a systemd unit file:

```ini
# /etc/systemd/system/my-velox-app.service
[Unit]
Description=My Velox Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/my-velox-app
EnvironmentFile=/var/www/my-velox-app/.env.production
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=my-velox-app

# Resource limits
LimitNOFILE=65536
MemoryMax=512M

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable my-velox-app
sudo systemctl start my-velox-app
sudo journalctl -u my-velox-app -f   # follow logs
```

## Nginx Configuration

```nginx
# /etc/nginx/sites-available/my-velox-app
upstream velox {
    server 127.0.0.1:3700;
    keepalive 32;
}

server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    # Long-lived cache for hashed static assets
    location ~ ^/assets/.*\.[0-9a-f]{8}\. {
        proxy_pass http://velox;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    location / {
        proxy_pass http://velox;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/my-velox-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com -d www.example.com
# Certbot automatically renews certificates via a cron job
```

## Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

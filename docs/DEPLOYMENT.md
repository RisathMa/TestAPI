# Nginx Deployment Guide

Deploy Clean Reader API behind Nginx as a reverse proxy.

## Prerequisites

- Ubuntu 20.04+ or similar Linux server
- Python 3.10+
- Nginx installed
- Domain with SSL certificate (Let's Encrypt recommended)

---

## 1. Server Setup

### Install System Dependencies

```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip nginx certbot python3-certbot-nginx
```

### Create Application User

```bash
sudo useradd -m -s /bin/bash cleanreader
sudo su - cleanreader
```

### Clone and Setup Application

```bash
cd /home/cleanreader
git clone <your-repo-url> api
cd api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn
```

### Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with production values

# Important: Set these for production
# DEBUG=false
# SECRET_KEY=<generate-secure-key>
# DATABASE_URL=postgresql://user:pass@localhost/cleanreader
```

---

## 2. Systemd Service

Create `/etc/systemd/system/cleanreader.service`:

```ini
[Unit]
Description=Clean Reader API
After=network.target

[Service]
User=cleanreader
Group=cleanreader
WorkingDirectory=/home/cleanreader/api
Environment="PATH=/home/cleanreader/api/venv/bin"
ExecStart=/home/cleanreader/api/venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind unix:/home/cleanreader/api/cleanreader.sock \
    --access-logfile /var/log/cleanreader/access.log \
    --error-logfile /var/log/cleanreader/error.log

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
sudo mkdir -p /var/log/cleanreader
sudo chown cleanreader:cleanreader /var/log/cleanreader

sudo systemctl daemon-reload
sudo systemctl enable cleanreader
sudo systemctl start cleanreader
sudo systemctl status cleanreader
```

---

## 3. Nginx Configuration

Create `/etc/nginx/sites-available/cleanreader`:

```nginx
# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

upstream cleanreader {
    server unix:/home/cleanreader/api/cleanreader.sock;
    keepalive 32;
}

server {
    listen 80;
    server_name api.yoursite.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yoursite.com;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.yoursite.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yoursite.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Logging
    access_log /var/log/nginx/cleanreader_access.log;
    error_log /var/log/nginx/cleanreader_error.log;

    # Max request size (for large content)
    client_max_body_size 10M;

    # API endpoints with rate limiting
    location /v1/ {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://cleanreader;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check (no rate limit)
    location /health {
        proxy_pass http://cleanreader;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # API docs
    location ~ ^/(docs|redoc|openapi.json) {
        proxy_pass http://cleanreader;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Root
    location / {
        proxy_pass http://cleanreader;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/cleanreader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 4. SSL Certificate

```bash
sudo certbot --nginx -d api.yoursite.com
```

---

## 5. Production Checklist

- [ ] Set `DEBUG=false` in `.env`
- [ ] Generate secure `SECRET_KEY`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure firewall (ufw)
- [ ] Set up log rotation
- [ ] Configure monitoring (e.g., Sentry)
- [ ] Set up automatic backups
- [ ] Configure CDN (Cloudflare recommended)

---

## Scaling

For high traffic (>1M requests/day):

1. **Horizontal Scaling**: Deploy multiple app servers behind a load balancer
2. **Database**: Use managed PostgreSQL (AWS RDS, DigitalOcean)
3. **Caching**: Add Redis for response caching
4. **CDN**: Cloudflare for DDoS protection and edge caching

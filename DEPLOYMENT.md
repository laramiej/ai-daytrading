# AI Day Trading System - Web Application Deployment Guide

**Date**: 2026-01-15
**Status**: Ready for Deployment
**Target**: Synology NAS via Portainer

---

## Overview

This guide covers deploying the AI Day Trading web application to your Synology NAS using Portainer. The application consists of:

- **FastAPI Backend** - REST API + WebSocket server (Port 8000)
- **React Frontend** - Modern web dashboard (Port 3000)
- **Trading Bot** - Integrated with web backend
- **Persistent Storage** - Logs and data stored on NAS

---

## Prerequisites

### On Synology NAS

✅ **Portainer installed and running**
- Access via http://your-nas-ip:9000

✅ **Docker installed via Package Center**
- Synology DSM 7.0+ recommended

✅ **Sufficient resources**
- 2GB RAM minimum (4GB recommended)
- 10GB storage for Docker images
- CPU: Any modern Synology NAS

### On Your Computer

✅ **Git installed** (to clone repository)
✅ **SSH access** to Synology NAS (optional but helpful)

---

## Deployment Methods

Choose one of these methods:

### Method 1: Portainer Stack (Recommended)

This is the easiest method - deploy everything with one click.

### Method 2: Docker Compose via SSH

More control, better for debugging.

---

## Method 1: Portainer Stack Deployment

### Step 1: Prepare Your Files

1. **On your computer**, navigate to the project:
```bash
cd /Users/jasonlaramie/Documents/MyCode/ai_daytrading
```

2. **Create a deployment package**:
```bash
# Create a zip file with all necessary files
tar -czf ai-trading-deploy.tar.gz \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.env' \
  .
```

3. **Transfer to Synology NAS**:
```bash
# Replace YOUR_NAS_IP and USERNAME
scp ai-trading-deploy.tar.gz USERNAME@YOUR_NAS_IP:/volume1/docker/ai-trading/
```

### Step 2: Extract on Synology

SSH into your Synology NAS:
```bash
ssh USERNAME@YOUR_NAS_IP
```

Extract the files:
```bash
cd /volume1/docker
mkdir -p ai-trading
cd ai-trading
tar -xzf ai-trading-deploy.tar.gz
```

### Step 3: Configure Environment

Create your `.env` file:
```bash
cp .env.example .env
nano .env
```

**IMPORTANT**: Fill in your actual API keys:
```env
# Alpaca
ALPACA_API_KEY=your_actual_alpaca_key_here
ALPACA_SECRET_KEY=your_actual_alpaca_secret_here
ALPACA_PAPER_TRADING=true

# Anthropic (or your preferred LLM)
ANTHROPIC_API_KEY=your_actual_anthropic_key_here

# Finnhub
FINNHUB_API_KEY=your_actual_finnhub_key_here

# Other settings (adjust as needed)
ENABLE_AUTO_TRADING=false
MAX_POSITION_SIZE=1000
MAX_DAILY_LOSS=500
```

### Step 4: Deploy via Portainer

1. Open Portainer in your browser: `http://YOUR_NAS_IP:9000`

2. Navigate to **Stacks** → **Add Stack**

3. **Name**: `ai-trading`

4. **Build method**: Select "Upload"

5. **Upload file**: Upload the `docker-compose.yml` file

6. **Environment variables** (optional - overrides .env):
   - Click "Add environment variable"
   - Add sensitive keys here instead of committing to .env

7. Click **Deploy the stack**

8. Wait for deployment (2-5 minutes)

### Step 5: Verify Deployment

Check container status:
- Portainer → Containers
- Should see:
  - `ai-trading-backend` (green/running)
  - `ai-trading-frontend` (green/running)

Access the application:
- Frontend: `http://YOUR_NAS_IP:3000`
- Backend API: `http://YOUR_NAS_IP:8000`
- API Docs: `http://YOUR_NAS_IP:8000/docs`

---

## Method 2: Docker Compose via SSH

### Step 1: SSH to Synology

```bash
ssh USERNAME@YOUR_NAS_IP
```

### Step 2: Create Project Directory

```bash
cd /volume1/docker
mkdir -p ai-trading
cd ai-trading
```

### Step 3: Clone Repository (or transfer files)

Option A - If you have git on Synology:
```bash
git clone YOUR_REPO_URL .
```

Option B - Transfer from your computer:
```bash
# On your computer
scp -r /Users/jasonlaramie/Documents/MyCode/ai_daytrading/* USERNAME@YOUR_NAS_IP:/volume1/docker/ai-trading/
```

### Step 4: Configure Environment

```bash
cp .env.example .env
nano .env
# Fill in your API keys
```

### Step 5: Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Step 6: Verify

```bash
# Check container status
docker-compose ps

# Test backend
curl http://localhost:8000/api/health

# View logs
docker-compose logs backend
docker-compose logs frontend
```

---

## Configuration

### Port Configuration

Default ports:
- **3000**: Frontend (React dashboard)
- **8000**: Backend (API + WebSocket)

To change ports, edit `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Change 8080 to your preferred port
  
  frontend:
    ports:
      - "3001:80"    # Change 3001 to your preferred port
```

### Volume Mounts

Data is persisted in these locations:
```
/volume1/docker/ai-trading/logs     → Trading logs
/volume1/docker/ai-trading/web/data → Database, cache
```

### Resource Limits

To limit resource usage, add to `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

---

## Accessing the Application

### From Local Network

- Dashboard: `http://YOUR_NAS_IP:3000`
- API: `http://YOUR_NAS_IP:8000`

### From Internet (Optional - Advanced)

⚠️ **Security Warning**: Only do this if you understand the risks!

1. **Set up HTTPS** (required for security):
   - Use Synology's built-in reverse proxy
   - Or use Nginx Proxy Manager container
   - Obtain SSL certificate (Let's Encrypt)

2. **Configure reverse proxy** in Synology DSM:
   - Control Panel → Login Portal → Advanced → Reverse Proxy
   - Create rule for port 3000 → your domain
   - Create rule for port 8000 → api.your domain

3. **Configure firewall**:
   - Only allow HTTPS (443)
   - Block direct access to ports 3000, 8000

---

## Monitoring & Maintenance

### View Logs

Portainer:
- Containers → Select container → Logs

Command line:
```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Services

Portainer:
- Containers → Select container → Restart

Command line:
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup

Important data to backup:
```bash
# Create backup
tar -czf ai-trading-backup-$(date +%Y%m%d).tar.gz \
  /volume1/docker/ai-trading/logs \
  /volume1/docker/ai-trading/web/data \
  /volume1/docker/ai-trading/.env

# Store in safe location
mv ai-trading-backup-*.tar.gz /volume1/backups/
```

---

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker-compose logs backend
```

Common issues:
- Missing .env file → Copy from .env.example
- Invalid API keys → Check .env values
- Port already in use → Change ports in docker-compose.yml
- Insufficient memory → Increase Docker memory limit

### Can't Access Frontend

1. Check container status:
```bash
docker-compose ps
```

2. Verify network connectivity:
```bash
curl http://localhost:3000
```

3. Check firewall rules in Synology DSM

4. Clear browser cache and reload

### Backend API Errors

1. Check backend logs:
```bash
docker-compose logs backend
```

2. Verify .env configuration

3. Test API directly:
```bash
curl http://localhost:8000/api/health
```

4. Check Alpaca API status (external service)

### WebSocket Connection Failed

1. Verify backend is running
2. Check WebSocket URL in frontend env
3. Ensure no proxy/firewall blocking WebSocket
4. Check browser console for errors

---

## Security Best Practices

✅ **Never commit .env file** - Contains sensitive API keys
✅ **Use strong passwords** for Portainer
✅ **Enable HTTPS** if exposing to internet
✅ **Regularly update** Docker images
✅ **Monitor logs** for suspicious activity
✅ **Use paper trading** until thoroughly tested
✅ **Backup regularly** - Especially .env and data

---

## Performance Optimization

### For Synology NAS

1. **Allocate sufficient memory to Docker**:
   - DSM → Docker → Settings → Limit RAM
   - Recommend 4GB minimum

2. **Use SSD cache** (if available):
   - Speeds up container I/O significantly

3. **Scheduled tasks** for cleanup:
   - DSM → Control Panel → Task Scheduler
   - Add: `docker system prune -f` (weekly)

---

## Portainer Stack Template

For easy deployment, use this Portainer stack template:

```yaml
# Copy the entire docker-compose.yml content here
# This can be pasted directly into Portainer's Stack editor
```

---

## Next Steps

After successful deployment:

1. ✅ Access dashboard at `http://YOUR_NAS_IP:3000`
2. ✅ Verify trading status
3. ✅ Review and adjust settings
4. ✅ Test with paper trading
5. ✅ Monitor performance for 1-2 weeks
6. ✅ Gradually enable auto-trading features

---

## Support & Updates

### Getting Help

- Check logs first
- Review Portainer container status
- Consult FastAPI docs: `http://YOUR_NAS_IP:8000/docs`

### Updating

The application is under active development. To update:

```bash
cd /volume1/docker/ai-trading
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

---

**Deployment Date**: 2026-01-15
**Documentation Version**: 1.0.0
**Tested On**: Synology DSM 7.x with Portainer 2.x


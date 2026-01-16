# Deploy AI Day Trading System from GitHub to Synology NAS via Portainer

This guide shows you how to deploy the AI Day Trading System directly from your GitHub repository to your Synology NAS using Portainer.

## Prerequisites

1. **Synology NAS** with Docker installed
2. **Portainer** installed and running on your Synology
3. **GitHub repository** with your code pushed
4. **SSH access** to your Synology NAS (for initial setup)

## Step 1: Push Your Code to GitHub

First, push all your code to GitHub (if not already done):

```bash
cd /Users/jasonlaramie/Documents/MyCode/ai_daytrading
git push origin main
```

## Step 2: Connect to Your Synology NAS via SSH

```bash
ssh your-username@your-synology-ip
```

## Step 3: Create Working Directory on Synology

```bash
# Create directory for the application
sudo mkdir -p /volume1/docker/ai-trading
cd /volume1/docker/ai-trading

# Clone your repository
sudo git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git .

# Or if you already have it cloned, pull latest changes
sudo git pull origin main
```

## Step 4: Create .env File on Synology

Create your `.env` file with your API keys:

```bash
sudo nano .env
```

Copy and paste your `.env` configuration:

```env
# Alpaca API Keys
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_PAPER_TRADING=true

# LLM API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Trading Configuration
DEFAULT_LLM_PROVIDER=anthropic
MAX_POSITION_SIZE=1000
MAX_DAILY_LOSS=500
MAX_TOTAL_EXPOSURE=5000
ENABLE_AUTO_TRADING=false

# Risk Management
STOP_LOSS_PERCENTAGE=2.0
TAKE_PROFIT_PERCENTAGE=5.0
MAX_OPEN_POSITIONS=5
ENABLE_SHORT_SELLING=true

# Sentiment Analysis
ENABLE_GOOGLE_TRENDS=true
FINNHUB_API_KEY=your_finnhub_api_key_here
ENABLE_FINNHUB=true

# Market Data
WATCHLIST=AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META,AMD,NFLX,SPY
```

Save and exit (Ctrl+X, then Y, then Enter).

## Step 5: Set Permissions

```bash
sudo chmod 600 .env
sudo chown -R YOUR-SYNOLOGY-USER:users /volume1/docker/ai-trading
```

## Step 6: Deploy via Portainer

### Option A: Using Portainer Stacks (Recommended)

1. **Open Portainer** in your browser:
   ```
   http://YOUR-SYNOLOGY-IP:9000
   ```

2. **Navigate to Stacks**:
   - Click on your environment (usually "local")
   - Click "Stacks" in the left menu
   - Click "+ Add stack"

3. **Configure the Stack**:
   - **Name**: `ai-trading-system`
   - **Build method**: Select "Repository"
   - **Repository URL**: `https://github.com/YOUR-USERNAME/YOUR-REPO-NAME`
   - **Repository reference**: `refs/heads/main`
   - **Compose path**: `docker-compose.yml`

4. **Add Environment Variables**:
   - Scroll down to "Environment variables"
   - Click "+ Add environment variable"
   - Add these variables:

   ```
   Name: STACK_DIR
   Value: /volume1/docker/ai-trading
   ```

5. **Click "Deploy the stack"**

### Option B: Using Git Repository in Portainer (Alternative)

If Option A doesn't work, use this method:

1. **Open Portainer** → **Stacks** → **+ Add stack**

2. **Name**: `ai-trading-system`

3. **Build method**: Select "Web editor"

4. **Paste this docker-compose configuration**:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: /volume1/docker/ai-trading
      dockerfile: Dockerfile.backend
    container_name: ai-trading-backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    env_file:
      - /volume1/docker/ai-trading/.env
    volumes:
      - /volume1/docker/ai-trading/logs:/app/logs
      - /volume1/docker/ai-trading/web/data:/app/data
      - /volume1/docker/ai-trading:/app
    restart: unless-stopped
    networks:
      - trading-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: /volume1/docker/ai-trading/web/frontend
      dockerfile: Dockerfile
    container_name: ai-trading-frontend
    depends_on:
      - backend
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=http://YOUR-SYNOLOGY-IP:8000
      - REACT_APP_WS_URL=ws://YOUR-SYNOLOGY-IP:8000
    restart: unless-stopped
    networks:
      - trading-network

networks:
  trading-network:
    driver: bridge
```

**Important**: Replace `YOUR-SYNOLOGY-IP` with your actual Synology IP address.

5. **Click "Deploy the stack"**

## Step 7: Monitor Deployment

1. Watch the deployment in Portainer:
   - The stack will build both containers
   - This may take 5-10 minutes the first time
   - Watch the logs for any errors

2. Check container logs:
   - Click on the stack name
   - Click on each container
   - Click "Logs" to see output

## Step 8: Access Your Application

Once deployed, access the web interface:

```
http://YOUR-SYNOLOGY-IP:3000
```

Backend API (for testing):
```
http://YOUR-SYNOLOGY-IP:8000/docs
```

## Step 9: Verify Everything Works

1. **Open the dashboard** at `http://YOUR-SYNOLOGY-IP:3000`
2. **Check the connection status** (should show "Connected")
3. **Navigate to Settings** and verify your configuration loaded
4. **Start the bot** and watch the activity feed

## Updating Your Application

When you make changes and want to update:

### Method 1: Via SSH

```bash
# SSH into Synology
ssh your-username@your-synology-ip

# Navigate to app directory
cd /volume1/docker/ai-trading

# Pull latest changes
sudo git pull origin main

# Restart containers via Portainer web UI
# Or use docker-compose
sudo docker-compose down
sudo docker-compose up -d --build
```

### Method 2: Via Portainer

1. Open Portainer → Stacks → ai-trading-system
2. Click "Pull and redeploy"
3. Or click "Stop" then "Deploy" again

## Troubleshooting

### Container Won't Start

**Check logs**:
```bash
sudo docker logs ai-trading-backend
sudo docker logs ai-trading-frontend
```

### Can't Access Web Interface

1. **Check ports are not blocked**:
   - Synology Firewall: Allow ports 3000 and 8000
   - Router: Port forwarding if accessing remotely

2. **Verify containers are running**:
   ```bash
   sudo docker ps
   ```

### Backend Shows "Trading system not initialized"

- **Verify .env file** exists and has valid API keys
- Check backend logs for specific errors

### Frontend Can't Connect to Backend

1. **Update frontend environment variables** in docker-compose.yml:
   ```yaml
   environment:
     - REACT_APP_API_URL=http://YOUR-SYNOLOGY-IP:8000
     - REACT_APP_WS_URL=ws://YOUR-SYNOLOGY-IP:8000
   ```

2. **Rebuild frontend**:
   ```bash
   sudo docker-compose up -d --build frontend
   ```

## Security Best Practices

1. **Change default ports** if exposing to internet:
   ```yaml
   ports:
     - "8080:8000"  # Backend
     - "8081:80"    # Frontend
   ```

2. **Use HTTPS** with reverse proxy (Nginx Proxy Manager or Traefik)

3. **Keep .env file secure**:
   ```bash
   sudo chmod 600 /volume1/docker/ai-trading/.env
   ```

4. **Never commit .env to GitHub**:
   - Already in `.gitignore`
   - Double-check: `git status` should not show `.env`

5. **Use strong Alpaca API keys** and keep them secure

## Automatic Updates (Optional)

Set up automatic git pulls on a schedule:

1. **Create update script**:
   ```bash
   sudo nano /volume1/docker/ai-trading/update.sh
   ```

2. **Add content**:
   ```bash
   #!/bin/bash
   cd /volume1/docker/ai-trading
   git pull origin main
   docker-compose down
   docker-compose up -d --build
   ```

3. **Make executable**:
   ```bash
   sudo chmod +x /volume1/docker/ai-trading/update.sh
   ```

4. **Add to Synology Task Scheduler**:
   - Open Synology DSM
   - Control Panel → Task Scheduler
   - Create → Scheduled Task → User-defined script
   - Schedule: Daily at 3 AM (or your preference)
   - Task: `/volume1/docker/ai-trading/update.sh`

## Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | Web dashboard |
| Backend API | 8000 | REST API & WebSocket |
| Portainer | 9000 | Container management |

## File Structure on Synology

```
/volume1/docker/ai-trading/
├── .env                          # Your API keys (DO NOT COMMIT)
├── .git/                         # Git repository
├── docker-compose.yml            # Container orchestration
├── Dockerfile.backend            # Backend container definition
├── requirements.txt              # Python dependencies
├── src/                          # Trading bot source code
├── web/
│   ├── backend/
│   │   └── app/
│   │       └── main.py          # FastAPI application
│   └── frontend/
│       ├── Dockerfile           # Frontend container definition
│       ├── package.json         # Node dependencies
│       └── src/                 # React application
├── logs/                        # Application logs (auto-created)
└── web/data/                    # Persistent data (auto-created)
```

## Next Steps

1. **Monitor the bot** via the activity feed
2. **Configure settings** via the Settings page
3. **Set up notifications** (future feature)
4. **Review trades** regularly
5. **Adjust risk parameters** as needed

## Support

For issues:
1. Check container logs in Portainer
2. Review backend logs: `sudo docker logs ai-trading-backend`
3. Check network connectivity between containers
4. Verify .env file has all required keys

## GitHub Repository Setup

If you haven't pushed to GitHub yet:

```bash
# On your local machine
cd /Users/jasonlaramie/Documents/MyCode/ai_daytrading

# Add remote (if not already added)
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git

# Push to GitHub
git push -u origin main
```

Remember to keep your `.env` file secure and NEVER commit it to GitHub!

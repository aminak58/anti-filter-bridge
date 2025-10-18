# 🚀 Deploy to Fly.io - Free Service

## Step 1: Install Fly CLI
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Or download from: https://fly.io/docs/hands-on/install-flyctl/
```

## Step 2: Login to Fly.io
```bash
fly auth login
# This will open browser for authentication
```

## Step 3: Deploy
```bash
# From project directory
fly launch

# Follow the prompts:
# - App name: anti-filter-bridge
# - Region: iad (Washington DC)
# - Deploy now: Yes
```

## Step 4: Test
```bash
# Get app URL
fly info

# Test health check
curl https://anti-filter-bridge.fly.dev/status

# Test WebSocket
python test_simple_ws.py
```

## Features
- ✅ 3 apps free
- ✅ No credit card required
- ✅ Global deployment
- ✅ High performance
- ✅ Auto-scaling
- ✅ Health checks

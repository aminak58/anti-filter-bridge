# 🚀 Deploy to Render - Free Service

## Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up with GitHub (no credit card required)

## Step 2: Deploy from GitHub
1. In Render Dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub repository: `aminak58/anti-filter-bridge`
4. Configure:
   - **Name**: `anti-filter-bridge`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m anti_filter_bridge.server --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`

## Step 3: Environment Variables
Add these environment variables in Render dashboard:
- `HOST`: `0.0.0.0`
- `PORT`: `8080` (Render sets this automatically)
- `LOG_LEVEL`: `INFO`

## Step 4: Deploy
1. Click "Create Web Service"
2. Wait for deployment to complete
3. Your app will be available at: `https://anti-filter-bridge.onrender.com`

## Step 5: Test
```bash
# Health check
curl https://anti-filter-bridge.onrender.com/status

# WebSocket test
python test_simple_ws.py
```

## Features
- ✅ Completely free
- ✅ No credit card required
- ✅ Auto-deploy from GitHub
- ✅ Custom domain support
- ✅ SSL certificate included
- ✅ Health checks

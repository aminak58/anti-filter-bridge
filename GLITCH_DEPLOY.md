# 🚀 Deploy to Glitch - 100% Free

## Step 1: Create Glitch Account
1. Go to [glitch.com](https://glitch.com)
2. Click "Sign up"
3. Sign up with GitHub (no credit card required)

## Step 2: Import from GitHub
1. In Glitch Dashboard, click "New Project"
2. Select "Import from GitHub"
3. Enter repository URL: `https://github.com/aminak58/anti-filter-bridge`
4. Click "Import from GitHub"

## Step 3: Configure
1. Glitch will automatically detect Python
2. The `package.json` file will configure the start command
3. Click "Show" to start the server

## Step 4: Keep Alive
1. Glitch apps sleep after 5 minutes of inactivity
2. Use a service like [UptimeRobot](https://uptimerobot.com) to ping your app every 5 minutes
3. Or use [cron-job.org](https://cron-job.org) to keep it alive

## Step 5: Get Public URL
1. Your app will be available at: `https://anti-filter-bridge.glitch.me`
2. You can customize the URL in project settings

## Step 6: Test
```bash
# Health check
curl https://anti-filter-bridge.glitch.me/status

# WebSocket test
python test_simple_ws.py
```

## Features
- ✅ 100% free forever
- ✅ No credit card required
- ✅ Custom domain support
- ✅ Auto-deploy from GitHub
- ✅ Built-in editor
- ✅ Real-time collaboration
- ⚠️ Sleeps after 5 minutes (but wakes up on request)

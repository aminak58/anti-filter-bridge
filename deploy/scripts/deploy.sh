#!/bin/bash

# Anti-Filter Bridge Deployment Script
# Run this script as root or with sudo

set -e

# Configuration
APP_USER="afb_user"
APP_GROUP="afb_group"
APP_DIR="/opt/anti-filter-bridge"
CONFIG_DIR="/etc/anti-filter-bridge"
LOG_DIR="/var/log/anti-filter-bridge"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Anti-Filter Bridge deployment...${NC}"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${YELLOW}Please run as root or with sudo${NC}"
    exit 1
fi

# Create user and group if they don't exist
if ! id -u $APP_USER > /dev/null 2>&1; then
    echo -e "${GREEN}Creating user and group...${NC}"
    groupadd $APP_GROUP
    useradd -r -g $APP_GROUP -s /bin/false $APP_USER
fi

# Create directories
echo -e "${GREEN}Creating directories...${NC}"
mkdir -p $APP_DIR
mkdir -p $CONFIG_DIR
mkdir -p $LOG_DIR
chown -R $APP_USER:$APP_GROUP $APP_DIR $LOG_DIR
chmod 750 $APP_DIR $LOG_DIR

# Install system dependencies
echo -e "${GREEN}Installing system dependencies...${NC}"
apt update
apt install -y python3-pip python3-venv nginx

# Set up Python virtual environment
echo -e "${GREEN}Setting up Python virtual environment...${NC}"
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}Installing Python dependencies...${NC}"
cp /path/to/requirements.txt .
pip install --upgrade pip
pip install -r requirements.txt

# Copy application files
echo -e "${GREEN}Copying application files...${NC}"
# Assuming the code is in the current directory
cp -r /path/to/anti_filter_bridge $APP_DIR/

# Set up configuration
echo -e "${GREEN}Setting up configuration...${NC}"
cp /path/to/.env $CONFIG_DIR/
chown -R $APP_USER:$APP_GROUP $CONFIG_DIR
chmod 640 $CONFIG_DIR/.env

# Set up systemd service
echo -e "${GREEN}Setting up systemd service...${NC}"
cp /path/to/anti-filter-bridge.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable anti-filter-bridge

# Set up Nginx
echo -e "${GREEN}Setting up Nginx...${NC}"
cp /path/to/anti-filter-bridge.conf /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/anti-filter-bridge.conf /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Start the service
echo -e "${GREEN}Starting Anti-Filter Bridge service...${NC}"
systemctl start anti-filter-bridge

# Show status
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${YELLOW}Service status:${NC}"
systemctl status anti-filter-bridge

echo -e "\n${GREEN}Anti-Filter Bridge has been deployed successfully!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Set up SSL certificates (e.g., using Let's Encrypt)"
echo "2. Configure your firewall to allow traffic on ports 80 and 443"
echo "3. Monitor logs: journalctl -u anti-filter-bridge -f"

exit 0

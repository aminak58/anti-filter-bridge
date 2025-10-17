# Anti-Filter Bridge Deployment Guide

This directory contains deployment scripts and configurations for the Anti-Filter Bridge server.

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- Systemd (for Linux service management)
- Nginx (recommended for production)
- SSL certificates (for HTTPS)

## Directory Structure

```
deploy/
├── config/               # Configuration files
│   ├── nginx/           # Nginx configuration
│   └── systemd/         # Systemd service files
├── scripts/             # Deployment scripts
├── .env.example        # Example environment variables
└── README.md           # This file
```

## Quick Start

1. Copy the example environment file and update it with your settings:
   ```bash
   cp .env.example .env
   nano .env
   ```

2. Install system dependencies:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv nginx
   ```

3. Set up a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r ../requirements.txt
   ```

4. Configure Nginx (see `config/nginx/anti-filter-bridge.conf`)

5. Set up systemd service (see `config/systemd/anti-filter-bridge.service`)

6. Start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable anti-filter-bridge
   sudo systemctl start anti-filter-bridge
   sudo systemctl status anti-filter-bridge
   ```

## Security Considerations

- Always use HTTPS in production
- Keep your system and dependencies updated
- Use strong passwords and API keys
- Regularly monitor logs
- Implement proper firewall rules

## Troubleshooting

Check the logs for errors:
```bash
journalctl -u anti-filter-bridge -f
```

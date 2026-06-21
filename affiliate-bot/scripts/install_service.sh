#!/bin/bash
# Affiliate Bot Systemd Service Installer
# Run this script to install the bot as a systemd service

set -e

BOT_USER="${BOT_USER:-$USER}"
BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${BOT_DIR}/venv"

echo "==================================="
echo "  Affiliate Bot Service Installer"
echo "==================================="
echo
echo "Installing for user: $BOT_USER"
echo "Bot directory: $BOT_DIR"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo ./install_service.sh)"
  exit 1
fi

# Create systemd service file
cat > /etc/systemd/system/affiliate-bot.service << EOF
[Unit]
Description=Affiliate Bot - Facebook Auto Commenter
After=network.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:$BOT_DIR/logs/bot.log
StandardError=append:$BOT_DIR/logs/bot-error.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Systemd service file created"

# Reload systemd
systemctl daemon-reload
echo "✅ Systemd reloaded"

# Enable service
systemctl enable affiliate-bot
echo "✅ Service enabled"

# Start service
systemctl start affiliate-bot
echo "✅ Service started"

# Show status
echo
echo "Service status:"
systemctl status affiliate-bot --no-pager

echo
echo "==================================="
echo "  Installation Complete!"
echo "==================================="
echo
echo "Useful commands:"
echo "  systemctl status affiliate-bot   - Check status"
echo "  systemctl stop affiliate-bot     - Stop bot"
echo "  systemctl restart affiliate-bot  - Restart bot"
echo "  journalctl -u affiliate-bot -f   - View logs"
echo
# 🚀 Deploy Guide - Affiliate Bot ke VPS

## 📋 Prerequisites

**VPS Specifications:**
- OS: Ubuntu 20.04+ / Debian 11+ (recommended)
- RAM: 1GB minimum (2GB recommended)
- Storage: 10GB+
- Python: 3.8+

---

## 🔹 OPTION 1: DOCKER DEPLOY (RECOMMENDED) ⭐

### **Step 1: Install Docker di VPS**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (optional, avoid sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

---

### **Step 2: Upload Project ke VPS**

**Option A: Git Clone (Recommended)**
```bash
# SSH ke VPS
ssh user@your-vps-ip

# Clone repository
git clone <your-repo-url> affiliate-bot
cd affiliate-bot
```

**Option B: SCP Upload**
```bash
# Dari local machine
scp -r affiliate-bot/ user@your-vps-ip:~/affiliate-bot
```

**Option C: SFTP (FileZilla, WinSCP)**
```
Host: your-vps-ip
Username: user
Password: ********
Path: /home/user/affiliate-bot
```

---

### **Step 3: Setup Environment Variables**

```bash
# Navigate to project
cd ~/affiliate-bot

# Copy example env
cp .env.example .env

# Edit .env file
nano .env
```

**Isi `.env`:**
```env
# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ADMIN_ID=987654321

# Facebook (Optional - bisa add via Telegram nanti)
FACEBOOK_COOKIES_PATH=./data/cookies

# AI Filter (Optional)
AI_API_KEY=sk-xxxxxxxxxxxxxx
AI_MODEL=gpt-4o-mini
USE_AI_FILTER=false

# Database
DATABASE_PATH=./data/affiliate.db

# Bot Settings
COMMENTS_PER_ACCOUNT_PER_DAY=20
MIN_DELAY_SECONDS=120
MAX_DELAY_SECONDS=600
OPERATING_START=9
OPERATING_END=20

# Logging
LOG_LEVEL=INFO
LOG_PATH=./logs
```

**Save & Exit:**
- `Ctrl + O` (save)
- `Enter` (confirm)
- `Ctrl + X` (exit)

---

### **Step 4: Build & Run Docker**

```bash
# Build Docker image
docker compose build

# Start containers
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

**Expected Output:**
```
[+] Running 2/2
 ✔ Container affiliate-bot-db    Started
 ✔ Container affiliate-bot-app   Started
```

---

### **Step 5: Verify Deployment**

```bash
# Check if bot is running
docker compose logs affiliate-bot-app | grep "Telegram bot started"

# Check database
docker compose exec affiliate-bot-db ls -la /app/data

# Check logs
docker compose logs -f affiliate-bot-app
```

**Test Telegram Bot:**
1. Open Telegram
2. Search bot username
3. Send `/start`
4. Should see menu!

---

### **Step 6: Auto-Start on Boot**

Docker compose already has `restart: unless-stopped`, jadi akan auto-restart.

**Verify:**
```bash
# Check restart policy
docker inspect affiliate-bot-app | grep -A 5 RestartPolicy

# Should show:
# "RestartPolicy": {
#     "Name": "unless-stopped",
#     "MaximumRetryCount": 0
# }
```

**Test reboot (optional):**
```bash
# Reboot VPS
sudo reboot

# After reboot, check if bot auto-starts
ssh user@your-vps-ip
docker compose ps
```

---

## 🔹 OPTION 2: MANUAL DEPLOY (Without Docker)

### **Step 1: Install Dependencies di VPS**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python & pip
sudo apt install -y python3 python3-pip python3-venv

# Install system dependencies
sudo apt install -y sqlite3 git curl

# Verify
python3 --version  # Should be 3.8+
pip3 --version
```

---

### **Step 2: Setup Project**

```bash
# Create directory
mkdir -p ~/affiliate-bot
cd ~/affiliate-bot

# Upload files (via SCP/SFTP) atau clone dari Git
# Git clone:
git clone <your-repo-url> .

# Create virtual environment
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### **Step 3: Setup Environment**

```bash
# Copy env file
cp .env.example .env

# Edit .env
nano .env

# (Same content as Docker option above)
```

---

### **Step 4: Create Systemd Service**

```bash
# Create service file
sudo nano /etc/systemd/system/affiliate-bot.service
```

**Isi service file:**
```ini
[Unit]
Description=Affiliate Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/affiliate-bot
Environment=PATH=/home/your-username/affiliate-bot/venv/bin
ExecStart=/home/your-username/affiliate-bot/venv/bin/python main.py
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=affiliate-bot

[Install]
WantedBy=multi-user.target
```

**Save & Exit:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

### **Step 5: Enable & Start Service**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable affiliate-bot

# Start service
sudo systemctl start affiliate-bot

# Check status
sudo systemctl status affiliate-bot
```

**Expected Output:**
```
● affiliate-bot.service - Affiliate Bot
     Loaded: loaded (/etc/systemd/system/affiliate-bot.service; enabled)
     Active: active (running) since Sun 2025-06-21 10:00:00 UTC
   Main PID: 12345 (python)
```

---

### **Step 6: Setup Log Rotation**

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/affiliate-bot
```

**Isi:**
```
/var/log/affiliate-bot/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 your-username your-username
}
```

---

## 🔹 MONITORING & MANAGEMENT

### **Docker Commands**

```bash
# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f affiliate-bot-app

# Restart bot
docker compose restart

# Stop bot
docker compose down

# Update & redeploy
git pull
docker compose build
docker compose up -d

# View resource usage
docker stats

# Access container shell
docker compose exec affiliate-bot-app bash

# View database
docker compose exec affiliate-bot-db sqlite3 /app/data/affiliate.db
```

---

### **Systemd Commands**

```bash
# View logs (real-time)
sudo journalctl -u affiliate-bot -f

# View last 100 lines
sudo journalctl -u affiliate-bot -n 100

# Restart bot
sudo systemctl restart affiliate-bot

# Stop bot
sudo systemctl stop affiliate-bot

# Start bot
sudo systemctl start affiliate-bot

# Check status
sudo systemctl status affiliate-bot

# View resource usage
top -p $(pgrep -f "python main.py")
```

---

## 🔹 SECURITY HARDENING

### **1. Setup Firewall (UFW)**

```bash
# Install UFW
sudo apt install ufw -y

# Allow SSH
sudo ufw allow ssh

# Allow only necessary ports
sudo ufw allow 22/tcp  # SSH

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

### **2. Setup Fail2Ban (Prevent Brute Force)**

```bash
# Install Fail2Ban
sudo apt install fail2ban -y

# Start service
sudo systemctl start fail2ban
sudo systemctl enable fail2ban

# Check status
sudo systemctl status fail2ban
```

---

### **3. Secure .env File**

```bash
# Restrict .env permissions
chmod 600 .env
chown your-username:your-username .env

# Verify
ls -la .env
# Should show: -rw------- 1 user user .env
```

---

### **4. Setup Automatic Security Updates**

```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades -y

# Enable
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## 🔹 BACKUP & RESTORE

### **Backup Database**

```bash
# Create backup script
nano ~/backup-bot.sh
```

**Isi script:**
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR

# Backup database
cp ~/affiliate-bot/data/affiliate.db $BACKUP_DIR/affiliate-bot_$DATE.db

# Backup cookies
tar -czf $BACKUP_DIR/cookies_$DATE.tar.gz ~/affiliate-bot/data/cookies/

# Keep only last 7 days
find $BACKUP_DIR -name "affiliate-bot_*.db" -mtime +7 -delete
find $BACKUP_DIR -name "cookies_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

**Make executable & schedule:**
```bash
chmod +x ~/backup-bot.sh

# Add to crontab
crontab -e

# Add line (backup daily at 3 AM):
0 3 * * * /home/user/backup-bot.sh
```

---

### **Restore Database**

```bash
# Stop bot
docker compose down
# OR
sudo systemctl stop affiliate-bot

# Restore database
cp ~/backups/affiliate-bot_20250101_030000.db ~/affiliate-bot/data/affiliate.db

# Start bot
docker compose up -d
# OR
sudo systemctl start affiliate-bot
```

---

## 🔹 TROUBLESHOOTING

### **Bot Tidak Start**

```bash
# Check logs
docker compose logs affiliate-bot-app
# OR
sudo journalctl -u affiliate-bot -n 50

# Common issues:
# 1. Missing .env file → Create .env
# 2. Wrong Telegram token → Verify token
# 3. Port already in use → Change port
```

---

### **Database Error**

```bash
# Check database file
ls -la data/affiliate.db

# Fix permissions
chmod 644 data/affiliate.db

# Test database
sqlite3 data/affiliate.db ".tables"
```

---

### **High Memory Usage**

```bash
# Check memory
docker stats
# OR
free -h

# Restart bot
docker compose restart
# OR
sudo systemctl restart affiliate-bot

# If still high, reduce features:
# - Disable AI filter (USE_AI_FILTER=false)
# - Reduce operating hours
```

---

### **Bot Lambat / Hang**

```bash
# Check CPU usage
top

# Check network
ping -c 4 facebook.com
ping -c 4 api.telegram.org

# Restart bot
docker compose restart
```

---

## 🔹 UPDATE & MAINTENANCE

### **Weekly Maintenance**

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Clean old logs
sudo journalctl --vacuum-time=7d

# 3. Clean Docker (if using Docker)
docker system prune -f

# 4. Check disk space
df -h

# 5. Check bot status
docker compose ps
# OR
sudo systemctl status affiliate-bot
```

---

### **Update Bot Code**

```bash
# Navigate to project
cd ~/affiliate-bot

# Pull latest code
git pull

# Rebuild (Docker)
docker compose build
docker compose up -d

# OR restart (Manual)
sudo systemctl restart affiliate-bot

# Check logs for errors
docker compose logs -f
# OR
sudo journalctl -u affiliate-bot -f
```

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] VPS ready (Ubuntu 20.04+)
- [ ] Docker installed (Option 1) OR Python installed (Option 2)
- [ ] Project uploaded to VPS
- [ ] `.env` file configured
- [ ] Bot running (`docker compose ps` or `systemctl status`)
- [ ] Telegram bot responds to `/start`
- [ ] Database created (`data/affiliate.db`)
- [ ] Logs accessible
- [ ] Auto-restart configured
- [ ] Firewall enabled
- [ ] Backup script scheduled
- [ ] Monitoring setup

---

## 📞 SUPPORT

**If something goes wrong:**

1. **Check logs first!**
   ```bash
   docker compose logs -f
   # OR
   sudo journalctl -u affiliate-bot -f
   ```

2. **Common fixes:**
   - Restart bot
   - Check `.env` configuration
   - Verify Telegram bot token
   - Check disk space (`df -h`)

3. **Still stuck?**
   - Save error logs
   - Check GitHub issues
   - Contact support

---

**Happy Deploy! 🎉**
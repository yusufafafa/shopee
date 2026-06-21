# 🛠️ Troubleshooting Guide

## Common Issues

### 1. Bot tidak start

**Symptom:** Error saat menjalankan `python main.py`

**Solutions:**
```bash
# Check dependencies
pip install -r requirements.txt

# Check .env file exists
ls -la .env

# Check Python version (need 3.8+)
python --version
```

### 2. Telegram bot tidak respond

**Symptom:** Bot tidak reply command di Telegram

**Solutions:**
- Pastikan `TELEGRAM_BOT_TOKEN` benar (dari @BotFather)
- Pastikan `TELEGRAM_ADMIN_ID` benar (cek dari @userinfobot)
- Restart bot

### 3. Facebook cookie invalid

**Symptom:** Error "Cookie validation failed"

**Solutions:**
- Pastikan cookie mengandung `c_user` dan `xs`
- Cookie expired, ambil ulang dari browser
- Format: `c_user=1000xxx;xs=38%3Axxx;fr=xxx;...`

### 4. AI filter tidak jalan

**Symptom:** Error OpenAI API

**Solutions:**
- Check `AI_API_KEY` di `.env`
- Pastikan ada quota OpenAI
- Atau disable AI filter (edit `src/core/config.py`)

### 5. Comment gagal post

**Symptom:** Auto-comment tidak terkirim

**Possible causes:**
- Akun Facebook diblokir/temporary ban
- Cookie expired
- Facebook detect automation

**Solutions:**
- Gunakan warm mode (`Warm: ON` di Telegram)
- Increase delay antara comments
- Rotate akun Facebook
- Check status dengan `/checklogin`

### 6. Memory leak / High RAM usage

**Symptom:** Bot consume banyak RAM setelah running lama

**Solutions:**
```bash
# Restart service
sudo systemctl restart affiliate-bot

# Or setup auto-restart
# Edit systemd service, add:
# RestartSec=3600  # Restart every hour
```

### 7. Database locked

**Symptom:** `sqlite3.OperationalError: database is locked`

**Solutions:**
```bash
# Stop bot
sudo systemctl stop affiliate-bot

# Remove database lock
rm data/affiliate.db-shm
rm data/affiliate.db-wal

# Start bot
sudo systemctl start affiliate-bot
```

## Logs Location

- **Systemd:** `journalctl -u affiliate-bot -f`
- **File logs:** `logs/affiliate_YYYYMMDD.log`
- **Docker:** `docker logs affiliate-bot`

## Getting Help

Jika masih ada masalah:

1. Check logs untuk error message
2. Screenshot error lengkap
3. Tanya di group/community

## Performance Tuning

### Optimize for VPS with low RAM (512MB-1GB)

```bash
# Limit Python memory
export PYTHONMALLOC=malloc

# Run with nice priority
nice -n 19 python main.py
```

### Increase scan speed

Edit `src/core/config.py`:
```python
SCAN_INTERVAL = 15  # Default 30 seconds
COMMENT_DELAY = 3   # Default 5 seconds
```

⚠️ **Warning:** Terlalu agresif bisa trigger Facebook ban!
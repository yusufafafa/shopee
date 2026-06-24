# Playwright Setup di VPS

## 📋 Prerequisites

Setelah pull code terbaru dari GitHub, ikuti langkah ini untuk setup Playwright.

---

## 🔹 Step 1: Install Dependencies

### Install Python dependencies
```bash
cd ~/shopee  # atau path project kamu
source venv/bin/activate  # jika pakai virtualenv
pip install -r requirements.txt
```

### Install Playwright browsers
```bash
playwright install chromium
```

Ini akan download Chromium (~150MB). Tunggu sampai selesai.

---

## 🔹 Step 2: Install System Dependencies

Playwright butuh beberapa library sistem untuk menjalankan browser:

```bash
# Ubuntu/Debian
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2
```

Atau pakai script otomatis dari Playwright:
```bash
playwright install-deps chromium
```

---

## 🔹 Step 3: Test Playwright

Buat test script sederhana:

```bash
nano test_playwright.py
```

Isi dengan:
```python
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with await async_playwright().start() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.facebook.com")
        print(f"Title: {await page.title()}")
        await browser.close()

asyncio.run(test())
```

Jalankan:
```bash
python test_playwright.py
```

Kalau berhasil, akan muncul title Facebook.

---

## 🔹 Step 4: Jalankan Bot

Setelah Playwright siap, jalankan bot seperti biasa:

```bash
# Dalam screen session
screen -S affiliate-bot

# Jalankan bot
python main.py

# Detach: Ctrl+A, lalu D
```

---

## 🔹 Troubleshooting

### Error: "Executable doesn't exist"
```bash
# Re-install Chromium
playwright install chromium --force
```

### Error: "Missing shared library"
```bash
# Install missing deps
playwright install-deps chromium
```

### Browser crash di VPS
Tambahkan flag di `scraper.py`:
```python
self.browser = await playwright.chromium.launch(
    headless=True,
    args=['--no-sandbox', '--disable-setuid-sandbox']
)
```

### Memory rendah
VPS dengan RAM < 2GB mungkin perlu swap:
```bash
# Create 2GB swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## ✅ Verifikasi

Setelah bot jalan, cek:
1. Bot tidak crash saat start
2. Log menunjukkan "Browser initialized successfully"
3. Postingan mulai ter-scrape (bukan 0 posts lagi)
4. Comment berhasil dipost

Kalau masih 0 posts, kemungkinan:
- Cookie expired → Add account baru via Telegram
- Account dibanned Facebook → Ganti account
- Group tidak accessible → Check group privacy
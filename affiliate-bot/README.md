# Affiliate Bot

Sistem auto-comment dan scraping Facebook dengan kontrol via Telegram. Didesain untuk deployment 24/7 di VPS.

## 📋 Fitur

- **Telegram Control Panel** - Kontrol bot via inline keyboard
- **AI Text Filter** - Klasifikasi postingan (pembeli vs penjual)
- **Facebook Auto-Comment** - Auto-reply dengan link affiliate
- **Multi-Account Support** - Kelola banyak akun Facebook
- **Warm Mode** - Delay lebih lama untuk menghindari ban
- **Real-time Notifications** - Update langsung ke Telegram
- **Statistics Tracking** - Tracking klik, order, komisi

## 🏗️ Arsitektur

```
affiliate-bot/
├── src/
│   ├── telegram/       # Telegram bot & handlers
│   ├── facebook/       # Scraper, commenter, cookies
│   ├── ai_filter/      # AI text classifier
│   ├── core/           # Config, logger, utilities
│   └── database/       # SQLite database layer
├── config/             # Configuration files
├── logs/               # Log files (auto-generated)
├── data/               # SQLite database (auto-generated)
├── scripts/            # Helper scripts
├── tests/              # Unit tests
├── main.py             # Entry point
├── requirements.txt    # Python dependencies
└── .env.example        # Environment template
```

## 🚀 Setup

### 1. Clone & Install

```bash
cd affiliate-bot
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` dan isi:

- `TELEGRAM_BOT_TOKEN` - Dari @BotFather
- `TELEGRAM_ADMIN_ID` - User ID Telegram kamu
- `AI_API_KEY` - OpenAI API key (optional, untuk AI filter)
- `FB_COOKIE` - Cookie Facebook (nanti bisa tambah via Telegram)

### 3. Dapatkan Facebook Cookie

1. Install extension **EditThisCookie** atau **Cookie Editor** di browser
2. Login Facebook dengan akun yang akan dipakai
3. Klik extension → Export cookie dalam format `key=value;`
4. Copy string cookie tersebut

### 4. Jalankan Bot

```bash
python main.py
```

## 📱 Cara Pakai

### Telegram Commands

1. **Start bot**: Kirim `/start` ke bot Telegram
2. **Tambah akun FB**: 
   - Kirim `/addaccount`
   - Atau langsung kirim cookie string ke chat
3. **Kontrol bot**: Gunakan inline keyboard untuk:
   - Toggle Auto ON/OFF
   - Toggle Warm ON/OFF
   - Cek status & statistik
   - Manage links, keywords, templates

### Flow Otomatis

1. Bot scan Facebook dengan keywords: "mau beli", "cari", "nyari", dll
2. Postingan difilter:
   - **Manual skip**: Terdeteksi sebagai penjual (jualan, promo, dll)
   - **AI skip**: Bukan pembeli (konfirmasi dengan AI)
3. Postingan valid → Auto-comment dengan link affiliate
4. Notifikasi terkirim ke Telegram

## 🔧 Configuration

### Keywords

Edit di `src/core/config.py`:

```python
BUYER_KEYWORDS = ["mau beli", "cari", "nyari", "butuh", "perlu"]
SELLER_KEYWORDS = ["jual", "dijual", "for sale", "open order"]
```

### Comment Templates

Edit di `src/ai_filter/prompts.py`:

```python
COMMENT_TEMPLATES = [
    "Ada nih kak, cek dulu 🔗 {link}",
    "Sebelum beli, cek ini dulu kak: {link} 🙏",
]
```

## 📊 Deployment di VPS

### Systemd Service (Linux)

Buat file `/etc/systemd/system/affiliate-bot.service`:

```ini
[Unit]
Description=Affiliate Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/affiliate-bot
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Jalankan:

```bash
sudo systemctl enable affiliate-bot
sudo systemctl start affiliate-bot
sudo systemctl status affiliate-bot
```

### Docker (Optional)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 🛠️ Development

### Run Tests

```bash
pytest tests/
```

### Add New Features

1. Buat branch baru
2. Implementasi fitur
3. Test dengan `pytest`
4. Commit & push

## ⚠️ Disclaimer

- Penggunaan bot ini mungkin melanggar ToS Facebook
- Gunakan dengan risiko sendiri
- Disarankan pakai warm mode dan delay yang cukup
- Rotate akun secara berkala untuk menghindari ban

## 📄 License

MIT License
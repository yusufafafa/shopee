"""Telegram command handlers"""
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 *Selamat datang di Affiliate Bot!*\n\n"
        "Gunakan menu di bawah untuk mengontrol bot.",
        parse_mode='Markdown'
    )


async def cmd_addaccount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /addaccount command"""
    await update.message.reply_text(
        "👥 *Tambah Akun Facebook*\n\n"
        "*Cara 1:* Kirim cookie dengan format:\n"
        "`c_user=xxx;xs=xxx;fr=xxx;...`\n\n"
        "*Cara 2:* Reply message yang berisi cookie.\n\n"
        "_Cookie bisa didapat dari browser pakai extension 'EditThisCookie' atau 'Cookie Editor'._",
        parse_mode='Markdown'
    )


async def cmd_checklogin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /checklogin command"""
    msg = await update.message.reply_text(
        "🔍 *Memeriksa login...*\n\n"
        "Silakan tunggu, sedang mengecek semua akun."
    )
    
    # Get all accounts from database
    from src.database.connection import Database
    db = Database()
    accounts = db.get_active_accounts()
    
    if not accounts:
        await msg.edit_text(
            "✅ *Hasil Check Login*\n\n"
            "Belum ada akun terdaftar.\n\n"
            "Kirim cookie Facebook untuk menambah akun:\n"
            "`c_user=xxx;xs=xxx;fr=xxx;...`",
            parse_mode='Markdown'
        )
        return
    
    # Check each account status
    account_list = []
    for i, acc in enumerate(accounts):
        today_stats = db.get_account_today_stats(acc.id)
        if today_stats["is_blocked"]:
            status = f"🚫 Blocked (sisa {today_stats.get('blocked_remaining', '12h')})"
        else:
            status = "✅ Aktif"
        account_list.append(f"Akun {i+1}: {acc.name} - {status}")
    
    await msg.edit_text(
        "✅ *Hasil Check Login*\n\n"
        + "\n".join(account_list) + "\n\n"
        "/checklogin untuk cek ulang",
        parse_mode='Markdown'
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    await update.message.reply_text(
        "📊 *Status Bot*\n\n"
        "🟢 Running\n"
        "Auto: ON\n"
        "Warm: OFF",
        parse_mode='Markdown'
    )


async def cmd_statistik(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /statistik command"""
    await update.message.reply_text(
        "📈 *Statistik Hari Ini*\n\n"
        "Postingan discan: 0\n"
        "Postingan ditemukan: 0\n"
        "Auto-comment terkirim: 0\n"
        "Manual skip (jualan): 0\n"
        "AI skip (bukan pembeli): 0",
        parse_mode='Markdown'
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "❓ *Bantuan*\n\n"
        "/start - Tampilkan menu utama\n"
        "/addaccount - Tambah akun Facebook\n"
        "/checklogin - Cek status login semua akun\n"
        "/status - Cek status bot\n"
        "/statistik - Lihat statistik hari ini\n"
        "/help - Tampilkan bantuan ini\n"
        "/cancel - Batalkan operasi yang sedang berjalan\n\n"
        "*Tips:*\n"
        "• Kirim cookie langsung ke chat untuk tambah akun\n"
        "• Gunakan Warm Mode untuk akun baru\n"
        "• Cek /statistik setiap hari",
        parse_mode='Markdown'
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command"""
    # Clear all awaiting states
    context.user_data.pop('awaiting_keyword', None)
    context.user_data.pop('awaiting_keyword_remove', None)
    context.user_data.pop('awaiting_link_url', None)
    context.user_data.pop('awaiting_link_product_name', None)
    context.user_data.pop('awaiting_link_remove', None)
    context.user_data.pop('temp_link_url', None)
    context.user_data.pop('awaiting_account_age', None)
    context.user_data.pop('awaiting_account_limit', None)
    context.user_data.pop('temp_account_id', None)
    context.user_data.pop('awaiting_setting', None)
    context.user_data.pop('awaiting_group_url', None)
    context.user_data.pop('awaiting_group_remove', None)
    context.user_data.pop('awaiting_account_remove', None)  # NEW
    
    await update.message.reply_text(
        "✅ *Operasi dibatalkan*\n\n"
        "Kembali ke menu utama dengan /start",
        parse_mode='Markdown'
    )


async def cmd_set_account_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle command to set custom account limit"""
    args = context.args
    if len(args) != 2:
        await update.message.reply_text(
            "❌ *Usage:* /setaccountlimit [account_id] [limit]\n\n"
            "Example: `/setaccountlimit 1 50`\n\n"
            "Or use interactive mode from [👤 Akun FB] menu.",
            parse_mode='Markdown'
        )
        return
    
    try:
        account_id = int(args[0])
        limit = int(args[1])
        
        from src.database.connection import Database
        db = Database()
        db.set_account_custom_limit(account_id, limit)
        
        await update.message.reply_text(
            f"✅ Custom limit set for Account ID {account_id}!\n\n"
            f"New daily limit: **{limit} comments/day**",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid input. Account ID and limit must be numbers.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_set_account_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle command to set account age"""
    args = context.args
    if len(args) != 2:
        await update.message.reply_text(
            "❌ *Usage:* /setaccountage [account_id] [days]\n\n"
            "Example: `/setaccountage 1 90` (90 days old)\n\n"
            "Or use interactive mode from [👤 Akun FB] menu.",
            parse_mode='Markdown'
        )
        return
    
    try:
        account_id = int(args[0])
        age_days = int(args[1])
        
        from src.database.connection import Database
        db = Database()
        db.set_account_age(account_id, age_days)
        
        # Auto-suggest limit based on age
        if age_days < 30:
            suggested = 20
            category = "New Account"
        elif age_days < 180:
            suggested = 50
            category = "Aged Account"
        else:
            suggested = 100
            category = "Established Account"
        
        await update.message.reply_text(
            f"✅ Account age set for Account ID {account_id}!\n\n"
            f"Age: **{age_days} days** ({category})\n"
            f"Suggested limit: {suggested} comments/day\n\n"
            f"Use /setaccountlimit {account_id} {suggested} to apply.",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid input. Account ID and age must be numbers.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    await update.message.reply_text(
        "⚙️ *Bot Settings*\n\n"
        "Gunakan menu di /start untuk mengubah pengaturan:\n"
        "📊 Daily Limit, ⏱️ Delay, 🕐 Operating Hours, dll.",
        parse_mode='Markdown'
    )


async def cmd_trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trending command - Show most searched products"""
    from src.database.connection import Database
    db = Database()
    
    # Get top searched keywords from database
    top_keywords = db.get_top_searched_keywords(limit=10)
    
    if top_keywords:
        trending_list = "\n".join([
            f"{i+1}. **{kw['keyword']}** - {kw['search_count']}x dicari"
            for i, kw in enumerate(top_keywords)
        ])
        
        await update.message.reply_text(
            f"🔥 *Produk Paling Sering Dicari*\n\n"
            f"{trending_list}\n\n"
            f"_Data real-time dari postingan Facebook_",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "📊 *Belum ada data pencarian*\n\n"
            "Bot akan menampilkan produk yang paling sering dicari setelah ada postingan yang diproses.",
            parse_mode='Markdown'
        )


async def cmd_removeaccount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /removeaccount command"""
    context.user_data['awaiting_account_remove'] = True
    
    # Get account list for display
    from src.database.connection import Database
    db = Database()
    accounts = db.get_all_accounts()
    
    if accounts:
        account_list = "\n".join([
            f"{i+1}. {acc.name} - {'✅ Aktif' if acc.is_active and not acc.is_blocked else '🚫 Nonaktif'}"
            for i, acc in enumerate(accounts)
        ])
        
        await update.message.reply_text(
            "🗑️ *Hapus Akun Facebook*\n\n"
            "Ketik **ID akun** yang mau dihapus:\n\n"
            f"{account_list}\n\n"
            "Contoh: ketik `1` untuk hapus akun pertama.\n\n"
            "Ketik /cancel untuk batal.",
            parse_mode='Markdown'
        )
    else:
        context.user_data.pop('awaiting_account_remove', None)
        await update.message.reply_text(
            "❌ Belum ada akun untuk dihapus.\n\n"
            "Tambahkan akun dulu dengan kirim cookie atau /addaccount.",
            parse_mode='Markdown'
        )


async def handle_cookie_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming cookie messages"""
    text = update.message.text
    
    # Check if message contains Facebook cookie
    if not text or "c_user=" not in text or "xs=" not in text:
        await update.message.reply_text(
            "❌ *Format cookie tidak valid!*\n\n"
            "Pastikan cookie mengandung `c_user` dan `xs`.\n"
            "Contoh: `c_user=1000xxx;xs=38xxx;fr=xxx`",
            parse_mode='Markdown'
        )
        return
    
    # Extract cookie
    cookie_str = text.strip()
    
    # Check if cookie already exists in database
    from src.database.connection import Database
    db = Database()
    existing_accounts = db.get_active_accounts()
    
    for acc in existing_accounts:
        if acc.cookie == cookie_str:
            await update.message.reply_text(
                f"ℹ️ *Cookie telah ada!*\n\n"
                f"Nama: `{acc.name}`\n"
                f"ID: `{acc.id}`\n"
                f"Status: {'✅ Aktif' if acc.is_active and not acc.is_blocked else '🚫 Nonaktif'}\n\n"
                "Tidak perlu tambah ulang.",
                parse_mode='Markdown'
            )
            return
    
    # Generate account name
    account_count = len(existing_accounts) + 1
    account_name = f"cookies{account_count}"
    
    # Save to database
    db.add_account(account_name, cookie_str)
    
    await update.message.reply_text(
        f"✅ *Akun berhasil ditambahkan!*\n\n"
        f"Nama: `{account_name}`\n"
        f"ID: `{account_count}`\n"
        f"Status: 🟢 Aktif\n\n"
        "Gunakan /checklogin untuk verifikasi.\n"
        "Gunakan /removeaccount untuk menghapus.",
        parse_mode='Markdown'
    )
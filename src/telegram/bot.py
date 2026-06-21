"""Telegram bot dengan inline keyboard"""
import asyncio
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from .handlers import (
    cmd_start, cmd_addaccount, cmd_checklogin,
    cmd_status, cmd_statistik, cmd_help, cmd_cancel, cmd_trending,
    cmd_settings, handle_cookie_message
)


class TelegramBot:
    """Telegram Control Panel Bot"""
    
    def __init__(self, token: str, admin_id: int):
        self.token = token
        self.admin_id = admin_id
        self.application: Optional[Application] = None
        self.is_auto_mode = False
        self.is_warm_mode = False
        self.stats = {
            "scanned": 0,
            "found": 0,
            "commented": 0,
            "manual_skip": 0,
            "ai_skip": 0
        }
        self.accounts = []  # List of Facebook accounts
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        keyboard = [
            [
                InlineKeyboardButton(f"Auto: {'✅ ON' if self.is_auto_mode else '❌ OFF'}", callback_data="toggle_auto"),
                InlineKeyboardButton(f"Warm: {'🔥 ON' if self.is_warm_mode else '❌ OFF'}", callback_data="toggle_warm"),
            ],
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("🧠 AI Status", callback_data="ai_status"),
            ],
            [
                InlineKeyboardButton("📈 Statistik", callback_data="statistik"),
                InlineKeyboardButton("🔥 Trending", callback_data="trending"),
            ],
            [
                InlineKeyboardButton("👥 Akun FB", callback_data="akun_fb"),
            ],
            [
                InlineKeyboardButton("🔗 Links", callback_data="links"),
                InlineKeyboardButton("🔑 Keywords", callback_data="keywords"),
            ],
            [
                InlineKeyboardButton("📝 Templates", callback_data="templates"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
            ],
            [
                InlineKeyboardButton("🚫 Blacklist", callback_data="blacklist"),
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🤖 *Affiliate Bot Control Panel*\n\n"
            "Kontrol bot affiliate Facebook Anda.\n\n"
            "Auto: Mode otomatis on/off\n"
            "Warm: Mode pemanasan akun (delay lebih lama)",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "toggle_auto":
            self.is_auto_mode = not self.is_auto_mode
            await query.edit_message_text(
                f"Auto mode: {'✅ ON' if self.is_auto_mode else '❌ OFF'}"
            )
        elif data == "toggle_warm":
            self.is_warm_mode = not self.is_warm_mode
            await query.edit_message_text(
                f"Warm mode: {'🔥 ON' if self.is_warm_mode else '❌ OFF'}"
            )
        elif data == "status":
            await query.edit_message_text(
                "📊 *Status Bot*\n\n"
                f"Auto Mode: {'✅ ON' if self.is_auto_mode else '❌ OFF'}\n"
                f"Warm Mode: {'🔥 ON' if self.is_warm_mode else '❌ OFF'}\n"
                "Status: 🟢 Running",
                parse_mode='Markdown'
            )
        elif data == "ai_status":
            await query.edit_message_text(
                "🧠 *AI Filter Status*\n\n"
                "Model: Active\n"
                "Last check: Just now",
                parse_mode='Markdown'
            )
        elif data == "statistik":
            # In production: fetch from database
            await query.edit_message_text(
                f"📈 *Statistik Hari Ini*\n\n"
                f"Postingan discan: {self.stats['scanned']}\n"
                f"Postingan ditemukan: {self.stats['found']}\n"
                f"Auto-comment terkirim: {self.stats['commented']}\n"
                f"Manual skip (jualan): {self.stats['manual_skip']}\n"
                f"AI skip (bukan pembeli): {self.stats['ai_skip']}",
                parse_mode='Markdown'
            )
        elif data == "trending":
            # Show trending searched products
            await query.edit_message_text(
                "🔥 *Produk Trending*\n\n"
                "Fitur ini menampilkan produk yang paling sering dicari dari postingan Facebook.\n\n"
                "Gunakan command `/trending` untuk melihat detail.",
                parse_mode='Markdown'
            )
        elif data == "akun_fb":
            account_list = "\n".join([
                f"{i+1}. {acc['name']} {'✅' if acc['active'] else '🚫'} — {acc['status']}"
                for i, acc in enumerate(self.accounts)
            ]) or "Belum ada akun terdaftar."
            
            await query.edit_message_text(
                f"👥 *Daftar Akun ({len(self.accounts)} total)*\n\n"
                f"{account_list}\n\n"
                "/checklogin untuk cek ulang",
                parse_mode='Markdown'
            )
        elif data == "links":
            links = self.db.get_all_affiliate_links() if hasattr(self, 'db') else []
            
            if links:
                link_list = "\n".join([
                    f"{i+1}. *{link.product_name}*\n"
                    f"   {link.url}\n"
                    f"   Category: {link.category} | Clicks: {link.clicks}"
                    for i, link in enumerate(links)
                ])
            else:
                link_list = "Belum ada link terdaftar."
            
            keyboard = [
                [InlineKeyboardButton("➕ Tambah Link", callback_data="link_add")],
                [InlineKeyboardButton("➖ Hapus Link", callback_data="link_remove")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="start")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🔗 *Daftar Link Affiliate* ({len(links)} total)\n\n"
                f"{link_list}\n\n"
                f"Pilih aksi di bawah:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        elif data == "link_add":
            context.user_data['awaiting_link_url'] = True
            await query.edit_message_text(
                "➕ *Tambah Link Affiliate*\n\n"
                "*Langkah 1:* Kirim link Shopee affiliate:\n"
                "Contoh: `https://shopee.co.id/product/123/456`\n\n"
                "Ketik /cancel untuk batal.",
                parse_mode='Markdown'
            )
        elif data == "link_remove":
            links = self.db.get_all_affiliate_links() if hasattr(self, 'db') else []
            
            if links:
                link_list = "\n".join([
                    f"{i+1}. {link.product_name} ({link.category})"
                    for i, link in enumerate(links)
                ])
                
                context.user_data['awaiting_link_remove'] = True
                
                await query.edit_message_text(
                    f"➖ *Hapus Link*\n\n"
                    f"Ketik **nomor** link yang mau dihapus:\n\n"
                    f"{link_list}\n\n"
                    "Ketik /cancel untuk batal.",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text(
                    "❌ Belum ada link untuk dihapus.",
                    parse_mode='Markdown'
                )
        elif data == "keywords":
            # Get keywords from config (hardcoded for now, will move to DB later)
            keywords = [
                "mau beli", "cari", "nyari", "butuh", "perlu",
                "rekomendasi", "suggest", "mohon saran"
            ]
            
            keyword_list = "\n".join([f"{i+1}. {kw}" for i, kw in enumerate(keywords)])
            
            keyboard = [
                [InlineKeyboardButton("➕ Tambah Keyword", callback_data="keyword_add")],
                [InlineKeyboardButton("➖ Hapus Keyword", callback_data="keyword_remove")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="start")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"🔑 *Keywords Monitoring*\n\n"
                f"Active keywords ({len(keywords)}):\n\n"
                f"{keyword_list}\n\n"
                f"Pilih aksi di bawah:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        elif data == "keyword_add":
            context.user_data['awaiting_keyword'] = True
            await query.edit_message_text(
                "➕ *Tambah Keyword*\n\n"
                "Ketik keyword yang mau ditambah:\n\n"
                "Contoh: `where to buy`, `looking for`, `need to buy`\n\n"
                "Ketik /cancel untuk batal.",
                parse_mode='Markdown'
            )
        elif data == "keyword_remove":
            keywords = [
                "mau beli", "cari", "nyari", "butuh", "perlu",
                "rekomendasi", "suggest", "mohon saran"
            ]
            
            keyword_list = "\n".join([f"{i+1}. {kw}" for i, kw in enumerate(keywords)])
            
            await query.edit_message_text(
                f"➖ *Hapus Keyword*\n\n"
                f"Ketik **nomor** keyword yang mau dihapus:\n\n"
                f"{keyword_list}\n\n"
                "Contoh: ketik `3` untuk hapus 'nyari'\n\n"
                "Ketik /cancel untuk batal.",
                parse_mode='Markdown'
            )
        elif data == "templates":
            await query.edit_message_text(
                "📝 *Template Komentar*\n\n"
                "1. \"Ada nih kak, cek dulu 🔗 {link}\"\n"
                "2. \"Sebelum beli, cek ini dulu kak: {link} 🙏\"\n"
                "3. \"Coba lihat di sini kak: {link}\"",
                parse_mode='Markdown'
            )
        elif data == "settings":
            # Show current settings
            settings_dict = self.settings.get_all_settings_dict()
            
            keyboard = [
                [InlineKeyboardButton("📊 Daily Limit", callback_data="set_daily_limit")],
                [InlineKeyboardButton("⏱️ Min Delay", callback_data="set_min_delay")],
                [InlineKeyboardButton("⏱️ Max Delay", callback_data="set_max_delay")],
                [InlineKeyboardButton("🕐 Operating Hours", callback_data="set_operating_hours")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="start")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"⚙️ *Bot Settings*\n\n"
                f"📊 Daily Limit: {settings_dict['comments_per_account_per_day']} comments/account\n"
                f"⏱️ Delay: {settings_dict['min_delay_seconds']}-{settings_dict['max_delay_seconds']}s\n"
                f"🕐 Operating: {settings_dict['operating_start']}:00 - {settings_dict['operating_end']}:00\n"
                f"👥 Min Accounts: {settings_dict['min_accounts_required']}\n\n"
                f"Klik button di bawah untuk edit:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        elif data == "blacklist":
            await query.edit_message_text(
                "🚫 *Blacklist*\n\n"
                "Belum ada akun/blacklist.",
                parse_mode='Markdown'
            )
        elif data == "help":
            await query.edit_message_text(
                "❓ *Bantuan*\n\n"
                "/start - Menu utama\n"
                "/addaccount - Tambah akun FB\n"
                "/checklogin - Cek login\n"
                "/status - Status bot\n"
                "/statistik - Statistik",
                parse_mode='Markdown'
            )
    
    async def send_posting_found(self, author: str, keyword: str, post_url: str):
        """Send 'Postingan Ditemukan!' notification"""
        if self.application:
            await self.application.bot.send_message(
                chat_id=self.admin_id,
                text=f"🔍 *Postingan Ditemukan!*\n\n"
                     f"👤 Author: {author}\n"
                     f"🏷️ Keyword: {keyword}\n\n"
                     f"🔗 {post_url}",
                parse_mode='Markdown'
            )
    
    async def send_filter_result(self, manual_skip: int, ai_skip: int):
        """Send filter scan result"""
        if self.application:
            await self.application.bot.send_message(
                chat_id=self.admin_id,
                text="🔍 *Filter hasil scan:*\n"
                     f"🚫 Manual skip: {manual_skip} (jualan)\n"
                     f"🧠 AI skip: {ai_skip} (bukan pembeli)",
                parse_mode='Markdown'
            )
    
    async def send_comment_sent(self, author: str, keyword: str, comment: str, post_url: str):
        """Send 'Auto-comment terkirim!' notification"""
        if self.application:
            await self.application.bot.send_message(
                chat_id=self.admin_id,
                text=f"✅ *Auto-comment terkirim!*\n\n"
                     f"👤 {author}\n"
                     f"🏷️ {keyword}\n"
                     f"💬 \"{comment}\"\n\n"
                     f"🔗 {post_url}",
                parse_mode='Markdown'
            )
    
    def add_account(self, name: str, cookie: str) -> bool:
        """Add Facebook account"""
        # Validate cookie
        if "c_user=" not in cookie or "xs=" not in cookie:
            return False
        
        self.accounts.append({
            "name": name,
            "cookie": cookie,
            "active": True,
            "status": "Aktif"
        })
        return True
    
    async def handle_keyword_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle keyword add/remove input"""
        text = update.message.text.strip()
        
        # Check if user is waiting for keyword input
        if context.user_data.get('awaiting_keyword'):
            # Add new keyword
            context.user_data.pop('awaiting_keyword', None)
            
            # In production: save to database
            if hasattr(self, 'db'):
                self.db.add_keyword(text)
            
            await update.message.reply_text(
                f"✅ Keyword *\"{text}\"* berhasil ditambahkan!\n\n"
                "Keyword akan aktif mulai sekarang.",
                parse_mode='Markdown'
            )
            return
        
        # Check if user wants to remove keyword by number
        if context.user_data.get('awaiting_keyword_remove'):
            context.user_data.pop('awaiting_keyword_remove', None)
            
            try:
                keyword_num = int(text)
                keywords = self.db.get_all_keywords() if hasattr(self, 'db') else [
                    "mau beli", "cari", "nyari", "butuh", "perlu",
                    "rekomendasi", "suggest", "mohon saran"
                ]
                
                if 1 <= keyword_num <= len(keywords):
                    removed_keyword = keywords[keyword_num - 1]
                    # In production: remove from database
                    if hasattr(self, 'db'):
                        self.db.remove_keyword(removed_keyword)
                    
                    await update.message.reply_text(
                        f"✅ Keyword *\"{removed_keyword}\"* berhasil dihapus!",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ Nomor tidak valid. Ketik angka antara 1-{len(keywords)}.",
                        parse_mode='Markdown'
                    )
            except ValueError:
                await update.message.reply_text(
                    "❌ Input tidak valid. Ketik **nomor** (angka), bukan nama keyword.",
                    parse_mode='Markdown'
                )
            return
        
        # Check if user is waiting for affiliate link URL
        if context.user_data.get('awaiting_link_url'):
            url = text
            context.user_data.pop('awaiting_link_url', None)
            context.user_data['awaiting_link_product_name'] = True
            context.user_data['temp_link_url'] = url
            
            await update.message.reply_text(
                "✅ Link diterima!\n\n"
                "*Langkah 2:* Ketik **nama produk** (WAJIB):\n"
                "Contoh: `Kemeja Slim Fit`, `Headphone Bluetooth`\n\n"
                "Ketik /cancel untuk batal.",
                parse_mode='Markdown'
            )
            return
        
        # Check if user is entering product name for affiliate link
        if context.user_data.get('awaiting_link_product_name'):
            product_name = text
            context.user_data.pop('awaiting_link_product_name', None)
            url = context.user_data.pop('temp_link_url', None)
            
            if url and hasattr(self, 'db'):
                # Add to database
                self.db.add_affiliate_link(url, product_name)
                
                await update.message.reply_text(
                    f"✅ Link affiliate berhasil ditambahkan!\n\n"
                    f"🔗 URL: `{url}`\n"
                    f"📦 Produk: *{product_name}*\n\n"
                    "Link akan dipakai untuk auto-comment.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ Gagal menambah link. Pastikan database tersedia.",
                    parse_mode='Markdown'
                )
            return
        
        # Check if user wants to remove affiliate link by number
        if context.user_data.get('awaiting_link_remove'):
            context.user_data.pop('awaiting_link_remove', None)
            
            try:
                link_num = int(text)
                links = self.db.get_all_affiliate_links() if hasattr(self, 'db') else []
                
                if 1 <= link_num <= len(links):
                    removed_link = links[link_num - 1]
                    self.db.remove_affiliate_link(removed_link.id)
                    
                    await update.message.reply_text(
                        f"✅ Link *\"{removed_link.product_name}\"* berhasil dihapus!",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        f"❌ Nomor tidak valid. Ketik angka antara 1-{len(links)}.",
                        parse_mode='Markdown'
                    )
            except ValueError:
                await update.message.reply_text(
                    "❌ Input tidak valid. Ketik **nomor** (angka), bukan nama produk.",
                    parse_mode='Markdown'
                )
            return
        
        # Check if message is a cookie (for account addition)
        if "c_user=" in text and "xs=" in text:
            from .handlers import handle_cookie_message
            await handle_cookie_message(update, context)
    
    def run(self):
        """Run the bot"""
        self.application = Application.builder().token(self.token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", cmd_start))
        self.application.add_handler(CommandHandler("addaccount", cmd_addaccount))
        self.application.add_handler(CommandHandler("checklogin", cmd_checklogin))
        self.application.add_handler(CommandHandler("status", cmd_status))
        self.application.add_handler(CommandHandler("statistik", cmd_statistik))
        self.application.add_handler(CommandHandler("trending", cmd_trending))
        self.application.add_handler(CommandHandler("help", cmd_help))
        self.application.add_handler(CommandHandler("cancel", cmd_cancel))
        
        # Add message handler for cookies
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_cookie_message
        ))
        
        # Add callback handler
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Add conversation handler for keyword management
        from telegram.ext import ConversationHandler, MessageHandler
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_keyword_input
        ))
        
        # Run bot
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
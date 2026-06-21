"""Database connection manager using SQLite"""
import sqlite3
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .models import FacebookAccount, Posting, Statistics, Keyword, AffiliateLink, CommentTemplate


class Database:
    """SQLite database manager"""
    
    def __init__(self, db_path: str = "./data/affiliate.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Facebook accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facebook_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                cookie TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_blocked BOOLEAN DEFAULT 0,
                blocked_until TIMESTAMP,
                last_used TIMESTAMP,
                total_comments INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                account_age_days INTEGER DEFAULT 0,
                custom_daily_limit INTEGER
            )
        """)
        
        # Postings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                content TEXT,
                keyword TEXT NOT NULL,
                post_url TEXT NOT NULL,
                is_seller BOOLEAN DEFAULT 0,
                is_buyer BOOLEAN DEFAULT 0,
                ai_filtered BOOLEAN DEFAULT 0,
                commented BOOLEAN DEFAULT 0,
                comment_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                date TEXT PRIMARY KEY,
                scanned INTEGER DEFAULT 0,
                found INTEGER DEFAULT 0,
                commented INTEGER DEFAULT 0,
                manual_skip INTEGER DEFAULT 0,
                ai_skip INTEGER DEFAULT 0,
                clicks INTEGER DEFAULT 0,
                orders INTEGER DEFAULT 0,
                commission REAL DEFAULT 0.0
            )
        """)
        
        # Keywords table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Affiliate links table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS affiliate_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                price REAL,
                clicks INTEGER DEFAULT 0,
                orders INTEGER DEFAULT 0,
                conversion_rate REAL DEFAULT 0.0,
                last_promoted TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Comment templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comment_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Searched keywords table (for analytics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS searched_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL UNIQUE,
                search_count INTEGER DEFAULT 0,
                last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Account daily limits tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                comment_count INTEGER DEFAULT 0,
                last_comment TIMESTAMP,
                is_blocked BOOLEAN DEFAULT 0,
                blocked_until TIMESTAMP,
                UNIQUE(account_id, date)
            )
        """)
        
        # Insert default keywords
        default_keywords = [
            "mau beli", "cari", "nyari", "butuh", "perlu",
            "rekomendasi", "suggest", "mohon saran"
        ]
        for kw in default_keywords:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO keywords (keyword) VALUES (?)",
                    (kw,)
                )
            except sqlite3.IntegrityError:
                pass  # Keyword already exists
        
        # Insert default comment templates
        default_templates = [
            "Ada nih kak, cek dulu 🔗 {link}",
            "Sebelum beli, cek ini dulu kak: {link} 🙏",
            "Coba lihat di sini kak: {link}",
            "Rekomendasi: {link} ✨",
            "Aku baru beli di sini, bagus kak: {link}"
        ]
        for template in default_templates:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO comment_templates (template) VALUES (?)",
                    (template,)
                )
            except sqlite3.IntegrityError:
                pass  # Template already exists
        
        conn.commit()
        conn.close()
    
    # Facebook Account operations
    def add_account(self, name: str, cookie: str) -> FacebookAccount:
        """Add new Facebook account"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO facebook_accounts (name, cookie) VALUES (?, ?)",
            (name, cookie)
        )
        conn.commit()
        account_id = cursor.lastrowid
        conn.close()
        return self.get_account(account_id)
    
    def get_account(self, account_id: int) -> Optional[FacebookAccount]:
        """Get account by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM facebook_accounts WHERE id = ?",
            (account_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_account(row)
        return None
    
    def get_all_accounts(self) -> List[FacebookAccount]:
        """Get all Facebook accounts"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facebook_accounts ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_account(row) for row in rows]
    
    def get_active_accounts(self) -> List[FacebookAccount]:
        """Get all active accounts"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM facebook_accounts WHERE is_active = 1 AND is_blocked = 0"
        )
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_account(row) for row in rows]
    
    def update_account_status(self, account_id: int, is_active: bool, is_blocked: bool = False, blocked_hours: int = None):
        """Update account status"""
        conn = self._get_connection()
        cursor = conn.cursor()
        blocked_until = None
        if is_blocked and blocked_hours:
            blocked_until = datetime.now().replace(second=0, microsecond=0)
            from datetime import timedelta
            blocked_until += timedelta(hours=blocked_hours)
        cursor.execute(
            "UPDATE facebook_accounts SET is_active = ?, is_blocked = ?, blocked_until = ? WHERE id = ?",
            (is_active, is_blocked, blocked_until, account_id)
        )
        conn.commit()
        conn.close()
    
    def increment_account_comments(self, account_id: int):
        """Increment comment count for account"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE facebook_accounts SET total_comments = total_comments + 1, last_used = CURRENT_TIMESTAMP WHERE id = ?",
            (account_id,)
        )
        conn.commit()
        conn.close()
    
    def set_account_age(self, account_id: int, age_days: int):
        """Set account age in days"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE facebook_accounts SET account_age_days = ? WHERE id = ?",
            (age_days, account_id)
        )
        conn.commit()
        conn.close()
    
    def set_account_custom_limit(self, account_id: int, limit: int):
        """Set custom daily limit for account"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE facebook_accounts SET custom_daily_limit = ? WHERE id = ?",
            (limit, account_id)
        )
        conn.commit()
        conn.close()
    
    def get_account_limit(self, account_id: int) -> int:
        """Get daily limit for account (custom or auto-calculated)"""
        account = self.get_account(account_id)
        if account:
            return account.get_daily_limit()
        return 20  # Default fallback
    
    def _row_to_account(self, row: sqlite3.Row) -> FacebookAccount:
        """Convert database row to FacebookAccount"""
        return FacebookAccount(
            id=row["id"],
            name=row["name"],
            cookie=row["cookie"],
            is_active=bool(row["is_active"]),
            is_blocked=bool(row["is_blocked"]),
            blocked_until=datetime.fromisoformat(row["blocked_until"]) if row["blocked_until"] else None,
            last_used=datetime.fromisoformat(row["last_used"]) if row["last_used"] else None,
            total_comments=row["total_comments"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            account_age_days=row["account_age_days"] if row["account_age_days"] else 0,
            custom_daily_limit=row["custom_daily_limit"]
        )
    
    # Posting operations
    def add_posting(self, author: str, content: str, keyword: str, post_url: str) -> Posting:
        """Add new posting"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO postings (author, content, keyword, post_url) VALUES (?, ?, ?, ?)",
            (author, content, keyword, post_url)
        )
        conn.commit()
        posting_id = cursor.lastrowid
        conn.close()
        return self.get_posting(posting_id)
    
    def get_posting(self, posting_id: int) -> Optional[Posting]:
        """Get posting by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM postings WHERE id = ?", (posting_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_posting(row)
        return None
    
    def mark_commented(self, posting_id: int, comment_text: str):
        """Mark posting as commented"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE postings SET commented = 1, comment_text = ? WHERE id = ?",
            (comment_text, posting_id)
        )
        conn.commit()
        conn.close()
    
    def _row_to_posting(self, row: sqlite3.Row) -> Posting:
        """Convert database row to Posting"""
        return Posting(
            id=row["id"],
            author=row["author"],
            content=row["content"],
            keyword=row["keyword"],
            post_url=row["post_url"],
            is_seller=bool(row["is_seller"]),
            is_buyer=bool(row["is_buyer"]),
            ai_filtered=bool(row["ai_filtered"]),
            commented=bool(row["commented"]),
            comment_text=row["comment_text"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )
    
    # Statistics operations
    def get_today_stats(self) -> Statistics:
        """Get today's statistics"""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM statistics WHERE date = ?", (today,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_stats(row)
        # Create new stats for today
        return Statistics(date=today)
    
    def update_stats(self, stats: Statistics):
        """Update statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO statistics 
            (date, scanned, found, commented, manual_skip, ai_skip, clicks, orders, commission)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stats.date, stats.scanned, stats.found, stats.commented,
            stats.manual_skip, stats.ai_skip, stats.clicks, stats.orders, stats.commission
        ))
        conn.commit()
        conn.close()
    
    def _row_to_stats(self, row: sqlite3.Row) -> Statistics:
        """Convert database row to Statistics"""
        return Statistics(
            date=row["date"],
            scanned=row["scanned"],
            found=row["found"],
            commented=row["commented"],
            manual_skip=row["manual_skip"],
            ai_skip=row["ai_skip"],
            clicks=row["clicks"],
            orders=row["orders"],
            commission=row["commission"]
        )
    
    # Keyword operations
    def get_all_keywords(self) -> list:
        """Get all active keywords"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM keywords WHERE is_active = 1 ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [row["keyword"] for row in rows]
    
    def add_keyword(self, keyword: str) -> bool:
        """Add new keyword"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO keywords (keyword) VALUES (?)",
                (keyword,)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False  # Keyword already exists
    
    def remove_keyword(self, keyword: str) -> bool:
        """Remove keyword"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM keywords WHERE keyword = ?",
            (keyword,)
        )
        conn.commit()
        conn.close()
        return True
    
    # Affiliate Link operations
    def add_affiliate_link(self, url: str, product_name: str, category: str = "General", price: float = None) -> AffiliateLink:
        """Add new affiliate link"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO affiliate_links (url, product_name, category, price) VALUES (?, ?, ?, ?)",
            (url, product_name, category, price)
        )
        conn.commit()
        link_id = cursor.lastrowid
        conn.close()
        return self.get_affiliate_link(link_id)
    
    def get_affiliate_link(self, link_id: int) -> AffiliateLink:
        """Get affiliate link by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM affiliate_links WHERE id = ?", (link_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_affiliate_link(row)
        return None
    
    def get_all_affiliate_links(self) -> list:
        """Get all active affiliate links"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM affiliate_links WHERE is_active = 1 ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_affiliate_link(row) for row in rows]
    
    def get_random_affiliate_link(self) -> AffiliateLink:
        """Get random active affiliate link"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM affiliate_links WHERE is_active = 1 ORDER BY RANDOM() LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_affiliate_link(row)
        return None
    
    def increment_link_clicks(self, link_id: int):
        """Increment click count for affiliate link"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE affiliate_links SET clicks = clicks + 1 WHERE id = ?",
            (link_id,)
        )
        conn.commit()
        conn.close()
    
    def update_link_promoted(self, link_id: int):
        """Update last_promoted timestamp"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE affiliate_links SET last_promoted = CURRENT_TIMESTAMP WHERE id = ?",
            (link_id,)
        )
        conn.commit()
        conn.close()
    
    def remove_affiliate_link(self, link_id: int) -> bool:
        """Remove affiliate link (soft delete)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE affiliate_links SET is_active = 0 WHERE id = ?",
            (link_id,)
        )
        conn.commit()
        conn.close()
        return True
    
    def _row_to_affiliate_link(self, row: sqlite3.Row) -> AffiliateLink:
        """Convert database row to AffiliateLink"""
        return AffiliateLink(
            id=row["id"],
            url=row["url"],
            product_name=row["product_name"],
            category=row["category"],
            price=row["price"],
            clicks=row["clicks"],
            orders=row["orders"],
            conversion_rate=row["conversion_rate"],
            last_promoted=datetime.fromisoformat(row["last_promoted"]) if row["last_promoted"] else None,
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )
    
    # Product search operations
    def search_links_by_name(self, keyword: str) -> list:
        """
        Search affiliate links by product name.
        Returns list of matched links.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Case-insensitive search
        search_term = f"%{keyword.lower().strip()}%"
        cursor.execute("""
            SELECT * FROM affiliate_links
            WHERE is_active = 1
            AND LOWER(product_name) LIKE ?
            ORDER BY RANDOM()
        """, (search_term,))
        
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_affiliate_link(row) for row in rows]
    
    def get_link_by_id(self, link_id: int) -> AffiliateLink:
        """Get specific affiliate link by ID"""
        return self.get_affiliate_link(link_id)
    
    # Comment Template operations
    def get_all_templates(self) -> list:
        """Get all active comment templates"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM comment_templates WHERE is_active = 1 ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        return [row["template"] for row in rows]
    
    def add_template(self, template: str) -> bool:
        """Add new comment template"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO comment_templates (template) VALUES (?)",
                (template,)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def remove_template(self, template_id: int) -> bool:
        """Remove template (soft delete)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE comment_templates SET is_active = 0 WHERE id = ?",
            (template_id,)
        )
        conn.commit()
        conn.close()
        return True
    
    def increment_template_usage(self, template_id: int):
        """Increment template usage count"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE comment_templates SET usage_count = usage_count + 1 WHERE id = ?",
            (template_id,)
        )
        conn.commit()
        conn.close()
    
    # Searched Keywords operations (Analytics)
    def track_keyword_search(self, keyword: str):
        """Track when a keyword is searched"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO searched_keywords (keyword, search_count, last_searched)
            VALUES (?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(keyword) DO UPDATE SET
                search_count = search_count + 1,
                last_searched = CURRENT_TIMESTAMP
        """, (keyword.lower().strip(),))
        conn.commit()
        conn.close()
    
    def get_top_searched_keywords(self, limit: int = 10) -> list:
        """Get most frequently searched keywords"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT keyword, search_count, last_searched
            FROM searched_keywords
            ORDER BY search_count DESC, last_searched DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [(row["keyword"], row["search_count"], row["last_searched"]) for row in rows]
    
    def get_all_searched_keywords(self) -> list:
        """Get all searched keywords with stats"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM searched_keywords ORDER BY search_count DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    # Account daily stats operations
    def get_account_today_stats(self, account_id: int) -> dict:
        """Get today's stats for specific account"""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT comment_count, is_blocked, blocked_until
            FROM account_daily_stats
            WHERE account_id = ? AND date = ?
        """, (account_id, today))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "comment_count": row["comment_count"],
                "is_blocked": bool(row["is_blocked"]),
                "blocked_until": datetime.fromisoformat(row["blocked_until"]) if row["blocked_until"] else None
            }
        else:
            return {"comment_count": 0, "is_blocked": False, "blocked_until": None}
    
    def increment_account_comment_count(self, account_id: int):
        """Increment comment count for account today"""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO account_daily_stats (account_id, date, comment_count, last_comment)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(account_id, date) DO UPDATE SET
                comment_count = comment_count + 1,
                last_comment = CURRENT_TIMESTAMP
        """, (account_id, today))
        conn.commit()
        conn.close()
    
    def mark_account_blocked(self, account_id: int, hours: int = 24):
        """Mark account as blocked"""
        today = datetime.now().strftime("%Y-%m-%d")
        blocked_until = datetime.now().replace(second=0, microsecond=0)
        from datetime import timedelta
        blocked_until += timedelta(hours=hours)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO account_daily_stats (account_id, date, is_blocked, blocked_until)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(account_id, date) DO UPDATE SET
                is_blocked = 1,
                blocked_until = ?
        """, (account_id, today, blocked_until, blocked_until))
        conn.commit()
        conn.close()
    
    def reset_account_block(self, account_id: int):
        """Reset account block status"""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE account_daily_stats
            SET is_blocked = 0, blocked_until = NULL
            WHERE account_id = ? AND date = ?
        """, (account_id, today))
        conn.commit()
        conn.close()
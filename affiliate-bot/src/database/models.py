"""Database models"""
from datetime import datetime
from typing import Optional


class FacebookAccount:
    """Facebook account model"""
    
    def __init__(
        self,
        id: int,
        name: str,
        cookie: str,
        is_active: bool = True,
        is_blocked: bool = False,
        blocked_until: datetime = None,
        last_used: datetime = None,
        total_comments: int = 0,
        created_at: datetime = None,
        account_age_days: int = 0,  # NEW: Track account age
        custom_daily_limit: int = None  # NEW: Custom limit per account
    ):
        self.id = id
        self.name = name
        self.cookie = cookie
        self.is_active = is_active
        self.is_blocked = is_blocked
        self.blocked_until = blocked_until
        self.last_used = last_used
        self.total_comments = total_comments
        self.created_at = created_at or datetime.now()
        self.account_age_days = account_age_days
        self.custom_daily_limit = custom_daily_limit
    
    def get_daily_limit(self) -> int:
        """Get daily limit based on account age or custom setting"""
        if self.custom_daily_limit:
            return self.custom_daily_limit
        
        # Auto-calculate based on age
        if self.account_age_days < 30:
            return 20  # New account: conservative
        elif self.account_age_days < 180:
            return 50  # Aged account: moderate
        else:
            return 100  # Established: aggressive
    
    def get_status(self) -> str:
        """Get account status string"""
        if self.is_blocked:
            if self.blocked_until and datetime.now() < self.blocked_until:
                remaining = self.blocked_until - datetime.now()
                hours = remaining.total_seconds() / 3600
                return f"🚫 Blocked (sisa {hours:.1f}h)"
            return "🚫 Blocked"
        if self.is_active:
            return "✅ Aktif"
        return "❌ Nonaktif"


class Posting:
    """Facebook posting model"""
    
    def __init__(
        self,
        id: int,
        author: str,
        content: str,
        keyword: str,
        post_url: str,
        is_seller: bool = False,
        is_buyer: bool = False,
        ai_filtered: bool = False,
        commented: bool = False,
        comment_text: Optional[str] = None,
        created_at: datetime = None
    ):
        self.id = id
        self.author = author
        self.content = content
        self.keyword = keyword
        self.post_url = post_url
        self.is_seller = is_seller
        self.is_buyer = is_buyer
        self.ai_filtered = ai_filtered
        self.commented = commented
        self.comment_text = comment_text
        self.created_at = created_at or datetime.now()


class Statistics:
    """Daily statistics model"""
    
    def __init__(
        self,
        date: str,
        scanned: int = 0,
        found: int = 0,
        commented: int = 0,
        manual_skip: int = 0,
        ai_skip: int = 0,
        clicks: int = 0,
        orders: int = 0,
        commission: float = 0.0
    ):
        self.date = date
        self.scanned = scanned
        self.found = found
        self.commented = commented
        self.manual_skip = manual_skip
        self.ai_skip = ai_skip
        self.clicks = clicks
        self.orders = orders
        self.commission = commission


class Keyword:
    """Keyword model for monitoring"""
    
    def __init__(
        self,
        id: int,
        keyword: str,
        is_active: bool = True,
        created_at: datetime = None
    ):
        self.id = id
        self.keyword = keyword
        self.is_active = is_active
        self.created_at = created_at or datetime.now()


class AffiliateLink:
    """Affiliate link model"""
    
    def __init__(
        self,
        id: int,
        url: str,
        product_name: str,
        category: str = "General",
        price: float = None,
        clicks: int = 0,
        orders: int = 0,
        conversion_rate: float = 0.0,
        last_promoted: datetime = None,
        is_active: bool = True,
        created_at: datetime = None
    ):
        self.id = id
        self.url = url
        self.product_name = product_name
        self.category = category
        self.price = price
        self.clicks = clicks
        self.orders = orders
        self.conversion_rate = conversion_rate
        self.last_promoted = last_promoted
        self.is_active = is_active
        self.created_at = created_at or datetime.now()


class CommentTemplate:
    """Comment template model"""
    
    def __init__(
        self,
        id: int,
        template: str,
        is_active: bool = True,
        usage_count: int = 0,
        created_at: datetime = None
    ):
        self.id = id
        self.template = template
        self.is_active = is_active
        self.usage_count = usage_count
        self.created_at = created_at or datetime.now()
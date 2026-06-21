"""AI text classifier for post filtering"""
import re
from typing import Tuple, Optional


class TextClassifier:
    """Classify Facebook posts as buyer or seller"""
    
    def __init__(self):
        # Manual filter patterns (no AI needed)
        self.seller_patterns = [
            r"\b(jual|dijual|for sale|open order|ready stock)\b",
            r"\b(harga|promo|diskon|murah|gross|grosir)\b",
            r"\b(ready|stok|stock|available)\b",
            r"🛒|🏪|📦|💰",
            r"https?://shopee\.|https?://tokopedia\.|https?://lazada\.",
        ]
        
        self.buyer_patterns = [
            r"\b(mau beli|cari|nyari|butuh|perlu)\b",
            r"\b(rekomendasi|suggest|mohon saran|ada yang)\b",
            r"\b(ada yang jual|toko|where to buy)\b",
        ]
        
        # Keyword extraction patterns
        # Captures the noun after buyer intent verbs
        self.keyword_extractors = [
            # "mau beli [kemeja]"
            r"(?:mau beli|ingin beli|mo beli)\s+([a-zA-Z\s]+?)(?:\s|$|yang|di|untuk)",
            # "cari [headphone bluetooth]"
            r"(?:cari|nyari|mencari)\s+([a-zA-Z\s]+?)(?:\s|$|yang|di|untuk|murah)",
            # "butuh [lampu tidur]"
            r"(?:butuh|perlu|memerlukan)\s+([a-zA-Z\s]+?)(?:\s|$|yang|di|untuk)",
            # "rekomendasi [jaket]"
            r"(?:rekomendasi|suggest|recommendation)\s+([a-zA-Z\s]+?)(?:\s|$|yang|di|untuk)",
        ]
    
    def extract_keyword(self, text: str) -> Optional[str]:
        """
        Extract product keyword from post content.
        Returns the main product noun/noun phrase.
        
        Examples:
        - "mau beli kemeja flanel" → "kemeja"
        - "cari headphone bluetooth murah" → "headphone"
        - "butuh lampu tidur LED" → "lampu"
        """
        text_lower = text.lower()
        
        # Try each extractor pattern
        for pattern in self.keyword_extractors:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                
                # Clean up: take first word only (main noun)
                # "kemeja flanel" → "kemeja"
                # "headphone bluetooth" → "headphone"
                main_keyword = extracted.split()[0] if extracted else None
                
                # Filter out stop words
                stop_words = ['yang', 'di', 'untuk', 'dan', 'atau', 'dengan', 'yang', 'ada']
                if main_keyword and main_keyword not in stop_words and len(main_keyword) > 2:
                    return main_keyword
        
        # Fallback: try to find any noun after buyer keyword
        buyer_match = re.search(
            r"(mau beli|cari|nyari|butuh|perlu|rekomendasi)\s+([a-zA-Z]+)",
            text_lower
        )
        if buyer_match:
            return buyer_match.group(2)
        
        return None
    
    def manual_filter(self, text: str) -> Tuple[bool, str]:
        """
        Manual filter without AI.
        Returns: (is_skip, reason)
        - (True, "seller") if post is from seller
        - (True, "not_buyer") if post is not from buyer
        - (False, "") if post passes manual filter (needs AI verification)
        """
        text_lower = text.lower()
        
        # Check seller patterns
        for pattern in self.seller_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return (True, "seller")
        
        # Check buyer patterns
        for pattern in self.buyer_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return (False, "")  # Passes manual filter
        
        # No buyer keyword found
        return (True, "not_buyer")
    
    async def ai_classify(self, text: str, api_key: str, model: str = "gpt-3.5-turbo") -> Tuple[bool, str]:
        """
        AI classification for posts that pass manual filter.
        Returns: (is_buyer, confidence_reason)
        """
        # Import here to avoid dependency if not using AI
        try:
            from openai import AsyncOpenAI
        except ImportError:
            return (False, "AI not available - OpenAI not installed")
        
        client = AsyncOpenAI(api_key=api_key)
        
        prompt = f"""
Analyze this Facebook post and determine if the author is:
1. A BUYER looking to purchase something
2. A SELLER promoting their products

Post: "{text}"

Respond with ONLY one word: BUYER or SELLER
"""
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            
            answer = response.choices[0].message.content.strip().upper()
            is_buyer = "BUYER" in answer
            
            return (is_buyer, "AI classified" if is_buyer else "AI rejected")
        
        except Exception as e:
            return (False, f"AI error: {str(e)}")
    
    async def classify(self, text: str, api_key: str = None, use_ai: bool = True) -> Tuple[bool, str, str]:
        """
        Full classification pipeline: manual filter → AI (optional).
        Returns: (should_comment, skip_type, reason)
        - should_comment: True if post is from buyer
        - skip_type: "manual" or "ai" or None
        - reason: "seller", "not_buyer", or AI reason
        """
        # Step 1: Manual filter
        is_skip, manual_reason = self.manual_filter(text)
        
        if is_skip:
            # Manual filter says skip
            if manual_reason == "seller":
                return (False, "manual", "seller")
            else:
                return (False, "manual", "not_buyer")
        
        # Step 2: AI filter (if enabled and API key provided)
        if use_ai and api_key:
            is_buyer, ai_reason = await self.ai_classify(text, api_key)
            if not is_buyer:
                return (False, "ai", ai_reason)
        
        # Passed all filters
        return (True, None, "buyer")
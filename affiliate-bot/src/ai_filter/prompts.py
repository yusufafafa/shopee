"""AI prompts for classification"""

CLASSIFICATION_PROMPT = """
Analyze this Facebook post and determine if the author is genuinely looking to buy something.

POST: "{text}"

CLASSIFICATION CRITERIA:
BUYER (should respond):
- Asking for product recommendations
- Looking for where to buy something
- Need help choosing a product
- Asking about availability

SELLER (should skip):
- Promoting their own products
- Sharing product links
- Using sales language (promo, diskon, etc.)
- Posting as a business/seller

Respond with ONLY one word: BUYER or SELLER
"""

COMMENT_TEMPLATES = [
    "Ada nih kak, cek dulu 🔗 {link}",
    "Sebelum beli, cek ini dulu kak: {link} 🙏",
    "Coba lihat di sini kak: {link}",
    "Rekomendasi: {link} ✨",
    "Aku baru beli di sini, bagus kak: {link}",
]

def get_comment_template(template_index: int = 0, link: str = "") -> str:
    """Get comment template with link"""
    if template_index < 0 or template_index >= len(COMMENT_TEMPLATES):
        template_index = 0
    return COMMENT_TEMPLATES[template_index].format(link=link)
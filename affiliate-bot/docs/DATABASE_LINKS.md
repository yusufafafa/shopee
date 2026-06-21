# 📦 DATABASE: AFFILIATE LINKS & PRODUCTS

## ✅ FITUR BARU YANG DITAMBAHKAN

### 1. **Table: `affiliate_links`**

Simpan link Shopee affiliate dengan detail produk.

**Schema:**
```sql
CREATE TABLE affiliate_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    product_name TEXT NOT NULL,      -- WAJIB!
    category TEXT DEFAULT 'General',
    price REAL,
    clicks INTEGER DEFAULT 0,
    orders INTEGER DEFAULT 0,
    conversion_rate REAL DEFAULT 0.0,
    last_promoted TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Fields:**
- `url`: Link Shopee affiliate (e.g., `https://shopee.co.id/product/123/456`)
- `product_name`: **WAJIB** - Nama produk (e.g., "Kemeja Slim Fit")
- `category`: Kategori produk (Fashion, Electronics, Home, dll)
- `price`: Harga produk (optional)
- `clicks`: Berapa kali link diklik
- `orders`: Berapa kali terjadi pembelian
- `conversion_rate`: Persentase conversion (orders/clicks)
- `last_promoted`: Kapan terakhir dipromosikan

---

### 2. **Table: `keywords`**

Simpan keywords untuk monitoring Facebook posts.

**Schema:**
```sql
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Default keywords:**
- mau beli, cari, nyari, butuh, perlu
- rekomendasi, suggest, mohon saran

---

### 3. **Table: `comment_templates`**

Simpan template komentar untuk variasi.

**Schema:**
```sql
CREATE TABLE comment_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Default templates:**
1. "Ada nih kak, cek dulu 🔗 {link}"
2. "Sebelum beli, cek ini dulu kak: {link} 🙏"
3. "Coba lihat di sini kak: {link}"
4. "Rekomendasi: {link} ✨"
5. "Aku baru beli di sini, bagus kak: {link}"

---

## 🎯 CARA PAKAI DARI TELEGRAM

### **TAMBAH LINK AFFILIATE**

1. **Klik button `[🔗 Links]`**
2. **Klik `[➕ Tambah Link]`**
3. **Bot akan request URL:**
   ```
   Langkah 1: Kirim link Shopee affiliate:
   Contoh: https://shopee.co.id/product/123/456
   ```
4. **Kirim URL:**
   ```
   https://shopee.co.id/product/123/456
   ```
5. **Bot akan request nama produk:**
   ```
   ✅ Link diterima!
   
   Langkah 2: Ketik nama produk (WAJIB):
   Contoh: Kemeja Slim Fit, Headphone Bluetooth
   ```
6. **Kirim nama produk:**
   ```
   Kemeja Slim Fit
   ```
7. **Bot confirm:**
   ```
   ✅ Link affiliate berhasil ditambahkan!
   
   🔗 URL: https://shopee.co.id/product/123/456
   📦 Produk: Kemeja Slim Fit
   
   Link akan dipakai untuk auto-comment.
   ```

---

### **HAPUS LINK AFFILIATE**

1. **Klik button `[🔗 Links]`**
2. **Klik `[➖ Hapus Link]`**
3. **Bot tampilkan list:**
   ```
   Ketik nomor link yang mau dihapus:
   
   1. Kemeja Slim Fit (Fashion)
   2. Headphone Bluetooth (Electronics)
   3. Lampu LED (Home)
   ```
4. **Ketik nomor:**
   ```
   2
   ```
5. **Bot confirm:**
   ```
   ✅ Link "Headphone Bluetooth" berhasil dihapus!
   ```

---

### **TAMBAH KEYWORD**

1. **Klik button `[🔑 Keywords]`**
2. **Klik `[➕ Tambah Keyword]`**
3. **Ketik keyword baru:**
   ```
   where to buy
   ```
4. **Bot confirm:**
   ```
   ✅ Keyword "where to buy" berhasil ditambahkan!
   ```

---

### **HAPUS KEYWORD**

1. **Klik button `[🔑 Keywords]`**
2. **Klik `[➖ Hapus Keyword]`**
3. **Bot tampilkan list:**
   ```
   Ketik nomor keyword yang mau dihapus:
   
   1. mau beli
   2. cari
   3. nyari
   4. butuh
   ```
4. **Ketik nomor:**
   ```
   3
   ```
5. **Bot confirm:**
   ```
   ✅ Keyword "nyari" berhasil dihapus!
   ```

---

### **BATALKAN OPERASI**

Ketik `/cancel` kapan saja untuk membatalkan operasi yang sedang berjalan.

---

## 📊 DATABASE OPERATIONS (Python API)

```python
from src.database.connection import Database

db = Database("./data/affiliate.db")

# === KEYWORDS ===
db.add_keyword("where to buy")
db.get_all_keywords()  # ['mau beli', 'cari', ...]
db.remove_keyword("nyari")

# === AFFILIATE LINKS ===
db.add_affiliate_link(
    url="https://shopee.co.id/product/123/456",
    product_name="Kemeja Slim Fit",
    category="Fashion",
    price=150000
)

db.get_all_affiliate_links()  # List of AffiliateLink objects
db.get_random_affiliate_link()  # Random active link

db.increment_link_clicks(link_id=1)
db.update_link_promoted(link_id=1)
db.remove_affiliate_link(link_id=1)  # Soft delete

# === TEMPLATES ===
db.add_template("Check this out: {link}")
db.get_all_templates()  # List of template strings
db.remove_template(template_id=1)
db.increment_template_usage(template_id=1)
```

---

## 🔄 ROTASI LINK OTOMATIS

Bot akan **rotate links** secara otomatis saat comment:

```python
# Di auto-commenter loop:
link = db.get_random_affiliate_link()
template = random.choice(db.get_all_templates())
comment = template.format(link=link.url)

# Update stats:
db.increment_link_clicks(link.id)
db.update_link_promoted(link.id)
```

**Contoh output:**
```
Post 1: "Ada nih kak, cek dulu 🔗 https://shopee.co.id/product/123/456"
Post 2: "Sebelum beli, cek ini dulu kak: https://shopee.co.id/product/789/012 🙏"
Post 3: "Rekomendasi: https://shopee.co.id/product/345/678 ✨"
```

---

## 📈 ANALYTICS (FUTURE ENHANCEMENT)

Table `affiliate_links` sudah support analytics:

- **Click tracking**: `db.increment_link_clicks(link_id)`
- **Order tracking**: Track dari Shopee API (optional)
- **Conversion rate**: `orders / clicks * 100`
- **Last promoted**: Kapan terakhir dipromosikan

**Contoh query:**
```python
# Top performing links:
links = db.get_all_affiliate_links()
for link in links:
    conversion = (link.orders / link.clicks * 100) if link.clicks > 0 else 0
    print(f"{link.product_name}: {conversion}% conversion")
```

---

## 🎯 NEXT STEPS

1. **Click tracking** - Track clicks via redirect service
2. **Order sync** - Sync dengan Shopee API untuk orders
3. **Smart rotation** - Prioritize high-converting links
4. **Category filtering** - Match link category dengan post keyword
5. **A/B testing** - Test which templates convert better

---

## ✅ SUMMARY

| Fitur | Status | Cara Pakai |
|-------|--------|------------|
| Tambah link affiliate | ✅ Done | Telegram: `[🔗 Links]` → `[➕ Tambah Link]` |
| Hapus link affiliate | ✅ Done | Telegram: `[🔗 Links]` → `[➖ Hapus Link]` |
| Tambah keyword | ✅ Done | Telegram: `[🔑 Keywords]` → `[➕ Tambah Keyword]` |
| Hapus keyword | ✅ Done | Telegram: `[🔑 Keywords]` → `[➖ Hapus Keyword]` |
| Template komentar | ✅ Done | Auto-rotate dari database |
| Link rotation | ✅ Done | `get_random_affiliate_link()` |
| Click tracking | ✅ Ready | `increment_link_clicks()` |
| Analytics | 🔄 Ready (API ready, UI TBD) | Query database langsung |

**Database path:** `./data/affiliate.db`
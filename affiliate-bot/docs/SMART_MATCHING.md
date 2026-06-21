# 🚀 FITUR BARU: SMART PRODUCT MATCHING & ANALYTICS

## ✅ YANG SUDAH DIIMPLEMENTASI

### 1. **Keyword Extraction dari Post**
Bot sekarang bisa **extract product keyword** dari postingan Facebook secara otomatis.

**Contoh:**
```
Post: "mau beli kemeja flanel murah"
→ Extract: "kemeja"

Post: "cari headphone bluetooth yang bagus"
→ Extract: "headphone"

Post: "butuh lampu tidur LED"
→ Extract: "lampu"
```

**Cara kerja:**
- Classifier pakai regex patterns untuk identify buyer intent
- Extract noun utama setelah keyword ("mau beli", "cari", "butuh", dll)
- Return single keyword untuk matching

---

### 2. **Smart Product Matching (Opsi A - Random)**

Bot sekarang **match produk** berdasarkan nama, dengan fallback random.

**Flow:**
```
1. Post masuk: "mau beli kemeja flanel"
2. Extract keyword: "kemeja"
3. Search database: WHERE product_name LIKE '%kemeja%'
4. Found: 3 products
   - Kemeja Slim Fit
   - Kemeja Regular Fit
   - Kemeja Oversized
5. Random pick: Kemeja Slim Fit ✅
6. Post comment dengan link Kemeja Slim Fit
```

**Kalau tidak ada match:**
```
1. Post: "mau beli barang unik"
2. Extract: "barang"
3. Search: 0 matches ❌
4. Fallback: Random link dari semua produk
5. Post comment dengan link random
```

---

### 3. **Search Tracking Analytics**

Bot sekarang **track setiap keyword** yang dicari, untuk analytics.

**Database table baru:**
```sql
CREATE TABLE searched_keywords (
    id INTEGER PRIMARY KEY,
    keyword TEXT NOT NULL UNIQUE,
    search_count INTEGER DEFAULT 0,
    last_searched TIMESTAMP,
    created_at TIMESTAMP
)
```

**Setiap kali bot process post:**
```python
keyword = classifier.extract_keyword(post_content)
if keyword:
    db.track_keyword_search(keyword)
    # INSERT/UPDATE searched_keywords
    # search_count += 1
    # last_searched = NOW
```

---

### 4. **Trending Products Command**

Command baru: `/trending` untuk lihat produk paling sering dicari.

**Output:**
```
🔥 Produk Paling Sering Dicari (Hari Ini)

1. Kemeja - 15x dicari
   (terakhir: 2025-06-21 10:30:00)
2. Headphone - 12x dicari
   (terakhir: 2025-06-21 10:25:00)
3. Lampu - 8x dicari
   (terakhir: 2025-06-21 10:20:00)
4. Celana - 7x dicari
   (terakhir: 2025-06-21 10:15:00)
5. Sepatu - 5x dicari
   (terakhir: 2025-06-21 10:10:00)

Data real-time dari postingan Facebook
```

**Telegram button:**
- Menu utama → `[🔥 Trending]` button
- Click → Show top 10 trending products

---

## 📊 CONTOH PENGGUNAAN

### **Tambah Produk dengan Nama Spesifik**

1. **Klik `[🔗 Links]`**
2. **Klik `[➕ Tambah Link]`**
3. **Kirim URL:**
   ```
   https://shopee.co.id/product/123/456
   ```
4. **Ketik nama produk (WAJIB):**
   ```
   Kemeja Slim Fit Premium
   ```
5. **Bot confirm:**
   ```
   ✅ Link affiliate berhasil ditambahkan!
   
   🔗 URL: https://shopee.co.id/product/123/456
   📦 Produk: Kemeja Slim Fit Premium
   
   Link akan dipakai untuk auto-comment.
   ```

---

### **Tambah Produk Lain (Varian)**

Ulangi proses dengan nama berbeda:

```
Produk 1: Kemeja Slim Fit Premium
Produk 2: Kemeja Regular Fit Casual
Produk 3: Kemeja Oversized Street Style
```

**Semua produk dengan keyword "kemeja" akan di-match!**

---

### **Bot Process Post Otomatis**

**Scenario 1: Match Found**
```
Post Facebook: "mau beli kemeja untuk kondangan"
↓
Extract keyword: "kemeja"
↓
Search database: 3 matches (Slim Fit, Regular Fit, Oversized)
↓
Random pick: Kemeja Oversized Street Style
↓
Post comment: "Ada nih kak, cek dulu 🔗 {link}"
↓
Track search: "kemeja" count += 1
```

**Scenario 2: No Match (Fallback)**
```
Post Facebook: "butuh sepatu lari yang nyaman"
↓
Extract keyword: "sepatu"
↓
Search database: 0 matches ❌
↓
Fallback: Random link (misal: Headphone Bluetooth)
↓
Post comment: "Cek ini kak: {link}"
↓
Track search: "sepatu" count += 1
```

---

### **Lihat Trending Products**

**Command:** `/trending`

**Output:**
```
🔥 Produk Paling Sering Dicari

1. Kemeja - 25x dicari
   (terakhir: 2025-06-21 11:00:00)
2. Sepatu - 18x dicari
   (terakhir: 2025-06-21 10:55:00)
3. Headphone - 12x dicari
   (terakhir: 2025-06-21 10:50:00)
4. Lampu - 8x dicari
   (terakhir: 2025-06-21 10:45:00)
5. Celana - 7x dicari
   (terakhir: 2025-06-21 10:40:00)
```

**Insight:**
- "Kemeja" paling banyak dicari → tambah varian kemeja lebih banyak
- "Sepatu" banyak dicari tapi tidak ada produk → tambah link sepatu
- "Headphone" ada di database tapi jarang dicari → mungkin perlu promosi lebih

---

## 🔧 DATABASE OPERATIONS

### **Track Keyword Search**
```python
db.track_keyword_search("kemeja")
# INSERT/UPDATE searched_keywords
```

### **Get Top Trending**
```python
top_keywords = db.get_top_searched_keywords(limit=10)
# Returns: [("kemeja", 25, "2025-06-21 11:00:00"), ...]
```

### **Search Products by Name**
```python
matches = db.search_links_by_name("kemeja")
# Returns: List of AffiliateLink objects with "kemeja" in product_name
```

### **Get All Search Stats**
```python
all_keywords = db.get_all_searched_keywords()
# Returns: Full list of all tracked keywords with counts
```

---

## 📈 ANALYTICS USE CASES

### **1. Product Demand Analysis**
```
Query: SELECT keyword, search_count FROM searched_keywords ORDER BY search_count DESC

Result:
- Kemeja: 25 searches
- Sepatu: 18 searches
- Headphone: 12 searches

Action: Tambah produk kemeja & sepatu (high demand, low supply)
```

---

### **2. Trend Detection**
```
Query: SELECT keyword, last_searched FROM searched_keywords 
       WHERE last_searched > NOW() - INTERVAL 1 HOUR

Result:
- Kemeja: 10:00, 10:15, 10:30, 10:45, 11:00 (trending up!)
- Lampu: 10:45 (one-off)

Action: Kemeja sedang hot → prioritize kemeja links
```

---

### **3. Gap Analysis**
```
Query: Compare searched_keywords vs affiliate_links

Searched: Kemeja (25x), Sepatu (18x), Tas (15x)
In Database: Kemeja (3 products), Headphone (5 products)

Gap: Sepatu & Tas banyak dicari tapi tidak ada produk!

Action: Add affiliate links untuk Sepatu & Tas
```

---

## 🎯 NEXT FEATURES (FUTURE ENHANCEMENTS)

### **Phase 2: Smart Pick (Advanced Matching)**
```python
# Score-based selection instead of random
best_match = max(matches, key=lambda x: (
    x.match_score(keyword) * 0.5 +      # 50% relevance
    x.conversion_rate * 0.3 +            # 30% performance
    (1 / x.days_since_promoted) * 0.2    # 20% freshness
))
```

**Benefit:** Prioritize products yang:
- Exact match dengan keyword
- Conversion rate tinggi
- Lama tidak dipromosiin

---

### **Phase 3: Multi-Keyword Extraction**
```python
Post: "mau beli kemeja flanel lengan panjang"
Extract: ["kemeja", "flanel", "lengan panjang"]

Match: product_name contains ALL keywords
→ "Kemeja Flanel Lengan Panjang Premium" ✅
```

---

### **Phase 4: Category-Based Fallback**
```python
keyword = "kemeja"
category = KEYWORD_TO_CATEGORY["kemeja"]  # "Fashion"

# If no exact match, fallback to category
links = db.get_links_by_category("Fashion")
→ Return: Semua produk Fashion (Kemeja, Celana, Jaket, dll)
```

---

### **Phase 5: Conversion Tracking**
```sql
CREATE TABLE conversions (
    keyword TEXT,
    product_id INTEGER,
    clicked_at TIMESTAMP,
    ordered_at TIMESTAMP,
    commission REAL
)
```

**Track:**
- Keyword → Product → Click → Order → Commission
- ROI per keyword
- Best converting products

---

## ✅ SUMMARY

| Fitur | Status | Implementation |
|-------|--------|----------------|
| Keyword extraction | ✅ Done | `classifier.extract_keyword()` |
| Product search by name | ✅ Done | `db.search_links_by_name()` |
| Random pick from matches | ✅ Done | `random.choice(matches)` |
| Search tracking | ✅ Done | `db.track_keyword_search()` |
| Trending command | ✅ Done | `/trending` + button |
| Analytics UI | ✅ Done | Telegram inline keyboard |
| Smart pick (scoring) | 🔄 TODO | Phase 2 |
| Category fallback | 🔄 TODO | Phase 3 |
| Multi-keyword match | 🔄 TODO | Phase 4 |
| Conversion tracking | 🔄 TODO | Phase 5 |

---

## 🚀 CARA PAKAI

### **1. Tambah Produk**
```
[🔗 Links] → [➕ Tambah Link]
→ URL: https://shopee.co.id/product/...
→ Nama produk: Kemeja Slim Fit
```

### **2. Bot Jalan Otomatis**
```
Post masuk → Extract keyword → Match produk → Post comment → Track search
```

### **3. Cek Trending**
```
/trending
atau
Klik [🔥 Trending] di menu
```

### **4. Analisa & Action**
```
- Keyword banyak dicari tapi tidak ada produk → Tambah link
- Produk banyak di-database tapi jarang dicari → Promosi lebih
- Trending keyword naik → Prioritize produk related
```

---

**Database path:** `./data/affiliate.db`
**Tables:** `affiliate_links`, `searched_keywords`, `keywords`, `comment_templates`
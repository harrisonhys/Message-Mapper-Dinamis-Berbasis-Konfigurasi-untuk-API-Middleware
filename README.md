# Dynamic Message Mapper — Prototipe Penelitian

**Judul Penelitian:**
*Perancangan dan Evaluasi Message Mapper Dinamis Berbasis Konfigurasi untuk Integrasi REST API Multi-Partner*

**Metode:** Design Science Research Methodology (DSRM)
**Domain:** Integrasi Order dan Shipment ke Partner Logistik
**Tech Stack:** Python · FastAPI · SQLite · Pydantic

---

## Struktur Proyek

```
Dynamic Message Mapper/
├── src/
│   ├── main.py                  # FastAPI application entry point
│   ├── database.py              # Database setup (SQLite/SQLAlchemy)
│   ├── models.py                # ORM models
│   ├── engine/
│   │   ├── transformer.py       # Transformation Engine
│   │   ├── validator.py         # Schema Validator
│   │   └── adapter.py           # Partner Adapter
│   └── api/
│       ├── partners.py          # CRUD Partner API
│       ├── mappings.py          # CRUD Mapping Config API
│       ├── transform.py         # Transform & Preview API
│       └── logs.py              # Request/Response Log API
├── mock_partners/
│   ├── partner_a_config.json    # Flat JSON, snake_case
│   ├── partner_b_config.json    # Flat JSON, camelCase
│   ├── partner_c_config.json    # Nested JSON
│   ├── partner_d_config.json    # Format tanggal & phone berbeda
│   └── partner_e_config.json    # Kombinasi nested + transformasi
├── data/
│   ├── generate_data.py         # Generator 500 payload uji
│   └── test_payloads.json       # Dataset payload transaksi
├── experiments/
│   ├── baseline_mapper.py       # Hard-coded mapping (baseline)
│   ├── dynamic_mapper_test.py   # Dynamic mapper test runner
│   ├── run_experiments.py       # Eksekusi semua skenario S1–S4
│   └── statistical_analysis.py  # Uji statistik (Shapiro, t-test, Wilcoxon)
├── results/                     # Output CSV & JSON hasil eksperimen
├── paper/
│   └── draft_sinta4.md          # Draft artikel jurnal Sinta 4
└── requirements.txt
```

---

## Cara Menjalankan

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Jalankan server
```bash
cd src
uvicorn main:app --reload --port 8000
```

### 3. Akses dokumentasi API
Buka browser: http://localhost:8000/docs

### 4. Generate test data
```bash
python data/generate_data.py
```

### 5. Jalankan eksperimen
```bash
python experiments/run_experiments.py
```

### 6. Analisis statistik
```bash
python experiments/statistical_analysis.py
```

---

## Skenario Pengujian

| Skenario | Jumlah Partner | Jumlah Payload | Jumlah Field |
|----------|:--------------:|:--------------:|:------------:|
| S1       | 3              | 100            | 10           |
| S2       | 3              | 300            | 15           |
| S3       | 5              | 500            | 20           |
| S4       | 5              | 500            | 30           |

---

## Partner Simulasi

| Partner   | Karakteristik                                       |
|-----------|-----------------------------------------------------|
| Partner A | Flat JSON, snake_case                               |
| Partner B | Flat JSON, camelCase                                |
| Partner C | Nested JSON                                         |
| Partner D | Format tanggal dd/mm/yyyy & phone +62xxx            |
| Partner E | Nested JSON + mandatory field + transformasi nilai  |

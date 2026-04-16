# MedGenomics

A genomics-focused healthcare data management platform built with FastAPI, SQLAlchemy, and a Tailwind CSS frontend. Manages 5,000+ patient genomic records and 3,000+ lab supply items with real-time analytics, search, and export.

## Features

### Authentication
- User registration and login (`/register`, `/login`)
- HMAC-SHA256 token generation (stdlib only — no PyJWT dependency)
- 24-hour token expiration
- Role-based access: `admin`, `doctor`, `lab_tech`, `viewer`
- Protected write endpoints require `Authorization: Bearer <token>`

### Patient Management
- 5,000 patient records with genomic profiles
- Full CRUD: create, read, update, delete
- Real-time search by name, patient ID, or DNA marker
- Risk-level filtering: High (>80%), Moderate (40–80%), Low (<40%)
- Add/Edit patient modal with form validation
- Genomic data: 50+ real genes (BRCA1/2, TP53, APOE, MTHFR, etc.), zygosity, expression level, treatment

### Inventory Management
- 3,000 lab supply items across four categories
- Full CRUD with auth-protected writes
- Adjust stock quantity without full update (`PUT /api/inventory/{id}/adjust`)
- Real-time search and category/status filtering
- Stock status: Critical / Low / Healthy with color-coded indicators
- Reorder-point alerts

### Analytics & Export
- KPI dashboard: patient count, avg age, high-risk count, low-stock count
- Risk distribution and top conditions breakdown
- Export patient report to CSV (`GET /api/export/report`)
- Export analytics summary to CSV (`GET /api/analytics/export`)

### Security
- CORS restricted to `ALLOWED_ORIGINS` env var (never wildcard + credentials)
- XSS prevention: all API data rendered via `escapeHtml()`, no raw `innerHTML`
- Tailwind dynamic classes replaced with inline `style=` attributes (CDN build-time safe)
- Passwords stored as SHA256 hashes
- Token HMAC validated server-side on every protected request

---

## Project Structure

```
MedGenomics/
├── src/
│   └── main.py                 # FastAPI app: models, auth, all API and page routes
├── static/
│   ├── index.html              # Dashboard — KPI overview, activity feed
│   ├── patient-pool.html       # Patient cards, search/filter, Add/Edit modals
│   ├── inventory.html          # Supply cards, stock bars, Adjust/Order modals
│   ├── analytics.html          # Analytics charts, CSV export, prediction model
│   ├── genomic-records.html    # Genomic records table (gene, variant, risk, status)
│   ├── login.html              # Login page
│   └── register.html           # Registration page
├── scripts/
│   └── bulk_seed.py            # Bulk data seeder (SQLAlchemy; SQLite + PostgreSQL)
├── docker-compose.yml          # PostgreSQL + API orchestration
├── Dockerfile                  # API container
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
└── .gitignore
```

---

## Quick Start

### Local (SQLite — no Docker needed)

```bash
git clone https://github.com/atharvadevne123/MedGenomics.git
cd MedGenomics

pip install -r requirements.txt

python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

On first startup, 5 sample patients and 8 inventory items are seeded automatically.

Open **http://localhost:8000**

### Seed 5,000 patients + 3,000 inventory items

```bash
python3 scripts/bulk_seed.py
```

The script clears existing data and inserts fresh records. Works against SQLite by default; set `DATABASE_URL` for PostgreSQL.

### Docker (PostgreSQL)

```bash
cp .env.example .env          # fill in POSTGRES_PASSWORD and SECRET_KEY
docker compose up -d
```

---

## Environment Variables

Copy `.env.example` to `.env` and set:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./medgenomics.db` | SQLAlchemy connection string |
| `ALLOWED_ORIGINS` | `http://localhost:8000,...` | Comma-separated CORS origins |
| `SECRET_KEY` | *(change in prod)* | HMAC signing key for auth tokens |
| `POSTGRES_PASSWORD` | — | Required for Docker/PostgreSQL |

---

## API Reference

### Pages

| Method | Path | Description |
|---|---|---|
| GET | `/` | Dashboard |
| GET | `/patient-pool` | Patient management |
| GET | `/inventory` | Inventory management |
| GET | `/analytics` | Analytics dashboard |
| GET | `/genomic-records` | Genomic records table |
| GET | `/login` | Login page |
| GET | `/register` | Registration page |

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | `{"status": "healthy"}` |

### Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/register` | — | Register; returns token + user |
| POST | `/api/login` | — | Login; returns token + user |

### Patients

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/patients` | — | List all patients |
| POST | `/api/patients` | — | Create patient (ID auto-generated) |
| GET | `/api/patients/search` | — | Search: `?query=&risk_min=&risk_max=` |
| GET | `/api/patients/{id}` | — | Get single patient |
| PUT | `/api/patients/{id}` | Bearer | Update patient fields |
| DELETE | `/api/patients/{id}` | Bearer | Delete patient |

### Inventory

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/inventory` | — | List all inventory |
| POST | `/api/inventory` | Bearer | Create supply item |
| GET | `/api/inventory/search` | — | Search: `?query=&category=` |
| PUT | `/api/inventory/{id}/adjust` | — | Update `qty_on_hand` only |
| GET | `/api/inventory/{id}` | — | Get single item |
| PUT | `/api/inventory/{id}` | Bearer | Update all item fields |
| DELETE | `/api/inventory/{id}` | Bearer | Delete item |

### Export

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/export/report` | — | Patient data CSV download |
| GET | `/api/analytics/export` | — | Analytics summary CSV download |

---

## Database Schema

### `patients`

| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR PK | `MG-XXXXX-A` format |
| `name` | VARCHAR | |
| `age` | INTEGER | 18–95 |
| `risk_score` | FLOAT | 0–100 |
| `dna_marker` | VARCHAR | e.g. `BRCA1-del`, `APOE4` |
| `initials` | VARCHAR | |
| `conditions` | JSON | `{"Type 2 Diabetes": true, ...}` |
| `genomic_data` | JSON | genes, expression, treatment, location |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | auto-updated |

### `inventory`

| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR PK | `INV-XXXXX` format |
| `item_name` | VARCHAR | Full product name + lot number |
| `category` | VARCHAR | Reagents / Kits / Equipment / Consumables |
| `qty_on_hand` | INTEGER | |
| `reorder_point` | INTEGER | |
| `cost` | FLOAT | USD per unit |
| `location` | VARCHAR | Shelf / Freezer / Cabinet |
| `supplier` | VARCHAR | |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | auto-updated |

### `users`

| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR PK | UUID |
| `username` | VARCHAR UNIQUE | |
| `email` | VARCHAR UNIQUE | |
| `hashed_password` | VARCHAR | SHA256 |
| `role` | VARCHAR | viewer / admin / doctor / lab_tech |
| `created_at` | DATETIME | |

---

## Tech Stack

**Backend**
- Python 3.9+
- FastAPI 0.104+
- SQLAlchemy ORM (SQLite for local, PostgreSQL for production)
- Pydantic v2
- Uvicorn ASGI server

**Frontend**
- Vanilla JavaScript (ES6+)
- Tailwind CSS (CDN with `forms` + `container-queries` plugins)
- Google Fonts: Manrope + Inter
- Material Symbols Outlined icons
- No build step — all pages are single HTML files

**DevOps**
- Docker & Docker Compose
- PostgreSQL 16 Alpine (production)
- SQLite (local development)

---

## Bulk Seeding

`scripts/bulk_seed.py` uses SQLAlchemy directly (no `psycopg2` dependency) and works against both SQLite and PostgreSQL:

```bash
# Local SQLite (default)
python3 scripts/bulk_seed.py

# PostgreSQL
DATABASE_URL=postgresql://admin:pass@localhost:5432/medgenomics python3 scripts/bulk_seed.py
```

**What gets seeded:**

- **5,000 patients** — 100+ name combinations, 50+ real genes (BRCA1/2, TP53, APOE, MTHFR, MLH1, CFTR, HBB, etc.), 21 DNA markers, 36 conditions, 22 treatments, 10 hospital locations
- **3,000 inventory items** — 130+ real genomics lab products (Illumina kits, Qiagen reagents, NEB enzymes, PCR consumables) across 29 real suppliers with category-appropriate pricing

Inserts in batches of 500 with progress output. Clears existing data before seeding.

---

## Troubleshooting

**Port 8000 in use**
```bash
lsof -ti:8000 | xargs kill -9
```

**Schema mismatch after update**
```bash
rm medgenomics.db   # SQLite only — deletes and recreates on next startup
```

**Verify data counts**
```bash
curl http://localhost:8000/api/patients | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"
curl http://localhost:8000/api/inventory | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"
```

**Interactive API docs**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## Author

**Atharva Devne** — [@atharvadevne123](https://github.com/atharvadevne123)

## License

MIT

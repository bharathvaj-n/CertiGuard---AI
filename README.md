# CertiGuard AI

AI-powered certificate forgery detection system using OCR, image forensics, and machine learning.

---

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), SQLite, EasyOCR, OpenCV, scikit-learn
- **Frontend**: Next.js 16, TypeScript, Framer Motion, Lucide React

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # Edit .env and set SECRET_KEY
python setup_db.py            # Creates DB and seeds initial data
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Access the app at [http://localhost:3000](http://localhost:3000)

**Default login:** `admin` / `admin123`

---

## Features

- **JWT Authentication** — Secure login with protected routes
- **Certificate Upload** — Drag-and-drop PDF/image upload
- **OCR Extraction** — EasyOCR pipeline extracts candidate name, issuer, date, ID
- **Image Forensics** — ELA, edge inconsistency, noise and compression artifact scoring
- **Rule Engine** — Validates ID format, required fields, OCR confidence
- **ML Scoring** — Random Forest classifier produces 0-100 risk score
- **Verification DB** — Matches extracted data against known genuine records
- **PDF Reports** — Downloadable forensic report per verification
- **History & Audit** — Full verification archive with search and filter
- **Analytics Dashboard** — Live stats and engine health monitoring

---

## Project Structure

```
backend/
  app/
    api/          # FastAPI route handlers
    core/         # Config and DB session
    data/         # Dataset adapters for forensics and layout
    ml/           # ML classifier (train + predict)
    models/       # SQLAlchemy ORM models
    schemas/      # Pydantic request/response schemas
    services/     # OCR, forensics, layout, rule engine, report
  db/             # SQLite database (gitignored)
  setup_db.py     # DB init and seed script

frontend/
  src/
    app/          # Next.js App Router pages
    components/   # Shared components (Sidebar)
    config.ts     # API base URL config
```

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and set:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing secret (use a strong random string) |
| `DATABASE_URL` | SQLAlchemy DB URL (defaults to local SQLite) |

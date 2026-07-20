# CertiGuard AI

> AI-powered certificate forgery detection system using OCR, image forensics, and machine learning.

---

## Features

- **JWT Authentication** — Secure login with bcrypt-hashed passwords and protected routes
- **Certificate Upload** — Drag-and-drop PDF/image upload with file size and type validation
- **OCR Extraction** — EasyOCR pipeline with CLAHE + adaptive binarisation + deskew preprocessing; extracts candidate name, issuer, date, and certificate ID
- **Image Forensics** — Error Level Analysis (ELA), copy-move detection (ORB), edge inconsistency, noise scoring, and color consistency analysis
- **Rule Engine** — Validates ID format, required fields, and OCR confidence thresholds
- **ML Scoring** — GBM + Random Forest soft-voting ensemble produces a 0–100 risk score with 4-tier verdict (Genuine / Needs Manual Review / Suspicious / Likely Fake)
- **Explainability** — Top-5 feature reasons returned with every prediction
- **Verification DB** — Fuzzy-matches extracted data against known genuine records
- **PDF Reports** — Downloadable forensic report per verification
- **History & Audit** — Full verification archive with search and filter
- **Analytics Dashboard** — Live stats and engine health monitoring
- **Offline Resilience** — Frontend silently handles backend-offline state with user-friendly banners

---

## Architecture

```
Browser (Next.js)
      │  REST / JSON
      ▼
FastAPI Backend
  ├── OCR Service        (EasyOCR + OpenCV preprocessing)
  ├── Forensics Service  (ELA, copy-move, edge, noise, color)
  ├── Rule Engine        (field validation, ID format, confidence)
  ├── ML Classifier      (GBM + RF ensemble, 17 features)
  ├── Verification DB    (fuzzy match against genuine records)
  └── Report Service     (ReportLab PDF generation)
      │
      ▼
SQLite (async via aiosqlite)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS, Framer Motion, Lucide React |
| Backend | FastAPI, Python 3.10+, Uvicorn |
| Database | SQLite + SQLAlchemy (async) + aiosqlite |
| OCR | EasyOCR, OpenCV |
| ML | scikit-learn (GradientBoosting + RandomForest ensemble) |
| Auth | python-jose (JWT), passlib + bcrypt |
| Reports | ReportLab |
| PDF parsing | PyMuPDF (fitz) |

---

## Folder Structure

```
CertiGuard-AI/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers (auth, certificates, dashboard)
│   │   ├── core/             # Config (pydantic-settings) and async DB session
│   │   ├── data/             # Dataset adapters for forensics and layout scoring
│   │   ├── db/               # SQLite database (gitignored)
│   │   ├── ml/
│   │   │   ├── models/       # Trained classifier .pkl (gitignored)
│   │   │   ├── predict_classifier.py
│   │   │   └── train_classifier.py
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── services/         # OCR, forensics, layout, rule engine, report, explainability
│   ├── uploads/              # Uploaded certificates (gitignored)
│   ├── reports/              # Generated PDF reports (gitignored)
│   ├── .env.example          # Environment variable template
│   ├── requirements.txt
│   └── setup_db.py           # DB init and admin seed script
├── frontend/
│   └── src/
│       ├── app/              # Next.js App Router pages
│       │   ├── dashboard/    # Main dashboard, verify, history, analytics, settings
│       │   └── login/
│       └── components/       # Shared UI components (Sidebar)
├── .gitignore
├── package.json              # Root convenience scripts
└── README.md
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- pip

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/bharathvaj-n/CertiGuard---AI.git
cd CertiGuard---AI
```

### 2. Backend Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Open .env and set a strong SECRET_KEY

# Initialise the database and seed the admin user
python setup_db.py

# Train the ML classifier (required on first run)
python -m app.ml.train_classifier

# Start the backend server
python -m uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Access the app at **http://localhost:3000**

**Default credentials:** `admin` / `admin123`

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | JWT signing secret — use a strong random string (min 32 chars) |
| `DATABASE_URL` | No | SQLAlchemy async DB URL (defaults to local SQLite) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | JWT expiry in minutes (default: 30) |

Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Running Locally

| Command | Description |
|---|---|
| `python -m uvicorn app.main:app --reload --port 8000` | Start backend (from `backend/`) |
| `npm run dev` | Start frontend (from `frontend/`) |
| `python setup_db.py` | Re-seed database (from `backend/`) |
| `python -m app.ml.train_classifier` | Retrain ML model (from `backend/`) |

API docs available at **http://localhost:8000/docs**

---

## Screenshots

> Add screenshots here after deployment.

| Dashboard | Verify Certificate | Forensics Report |
|---|---|---|
| *(screenshot)* | *(screenshot)* | *(screenshot)* |

---

## Future Enhancements

- [ ] Multi-language OCR support (beyond English)
- [ ] Blockchain-based certificate registry for tamper-proof verification
- [ ] Batch upload and bulk verification
- [ ] Email notification on verification completion
- [ ] Role-based access control (admin / verifier / viewer)
- [ ] REST API for third-party integrations
- [ ] Docker Compose for one-command deployment
- [ ] Cloud storage (S3) for uploads and reports

---

## License

This project is licensed under the [MIT License](LICENSE).

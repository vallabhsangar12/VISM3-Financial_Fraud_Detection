# 🛡️ FraudShield — Enterprise Fraud Detection & Monitoring System

> **Task 4 | Vinayak IT Internship | Month 3**
> A production-ready, end-to-end fraud detection platform with real-time monitoring, ML inference, case management, and compliance reporting.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    FRAUDSHIELD ARCHITECTURE                      │
├──────────────────┬───────────────────────────────────────────────┤
│                  │                                               │
│  DATA SOURCES    │   ┌─────────────────────────────────────┐    │
│                  │   │      STREAMLIT DASHBOARD (8501)      │    │
│  creditcard.csv ─┤──▶│  • Live Transaction Feed             │    │
│  Stream Sim.    ─┤   │  • Risk Distribution Charts          │    │
│  API Payloads   ─┤   │  • Fraud Trend (7-Day)               │    │
│                  │   │  • Suspicious Accounts Table          │    │
│                  │   └──────────┬──────────────────────────-┘    │
│                  │              │ Pages                           │
│                  │   ┌──────────▼──────────────────────────┐    │
│                  │   │         MULTIPAGE APP                │    │
│                  │   │  1. Alert Management                  │    │
│                  │   │  2. Business Metrics & ROI            │    │
│                  │   │  3. Compliance & Reporting            │    │
│                  │   │  4. Fraud Pattern Analysis            │    │
│                  │   │  5. Investigation Workflow            │    │
│                  │   └──────────┬──────────────────────────-┘    │
│                  │              │ REST API calls                  │
│                  │   ┌──────────▼──────────────────────────┐    │
│                  │   │       FASTAPI BACKEND (8000)         │    │
│                  │   │  POST /predict    → ML inference     │    │
│                  │   │  GET  /alerts     → Alert CRUD       │    │
│                  │   │  POST /cases      → Case management  │    │
│                  │   │  POST /auth/token → JWT auth         │    │
│                  │   └──────────┬──────────────────────────-┘    │
│                  │              │                                 │
│                  │   ┌──────────▼──────────────────────────┐    │
│                  │   │        ML MODEL LAYER                │    │
│                  │   │  XGBoost / Random Forest             │    │
│                  │   │  SMOTE oversampling                  │    │
│                  │   │  SHAP explainability                 │    │
│                  │   └──────────┬──────────────────────────-┘    │
│                  │              │                                 │
│                  │   ┌──────────▼──────────────────────────┐    │
│                  │   │        DATABASE (PostgreSQL)         │    │
│                  │   │  transactions | alerts | cases        │    │
│                  │   │  audit_logs | users | reports         │    │
│                  │   └─────────────────────────────────────┘    │
└──────────────────┴───────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Task4/
│
├── app.py                          ← Main Streamlit dashboard (Live Feed, KPIs, Charts)
│
├── backend/
│   ├── app_api.py                  ← FastAPI application entry point
│   ├── stream_simulator.py         ← Real-time transaction stream simulator
│   ├── explainability.py           ← SHAP-like feature contribution engine
│   ├── model/
│   │   ├── train_model.py          ← ML training pipeline (XGBoost + SMOTE)
│   │   └── fraud_model.pkl         ← Serialised model bundle (generated)
│   ├── routes/
│   │   ├── auth.py                 ← JWT authentication endpoints
│   │   ├── predict.py              ← POST /predict inference route
│   │   ├── alerts.py               ← Alert CRUD routes
│   │   └── cases.py                ← Case management routes
│   └── utils/
│       ├── logger.py               ← Structured JSON rotating logger
│       └── validators.py           ← Pydantic v2 request/response schemas
│
├── pages/
│   ├── 1_Alert_Management.py       ← Alert triage, assignment, case creation
│   ├── 2_Business_Metrics.py       ← ROI, precision/recall, savings charts
│   ├── 3_Compliance_Reporting.py   ← SHAP explainability, audit log, CSV export
│   ├── 4_Fraud_Pattern_Analysis.py ← High-freq accounts, amount anomalies, geo
│   └── 5_Investigation_Workflow.py ← Case management kanban board
│
├── database/
│   └── schema.sql                  ← PostgreSQL schema (6 tables + indexes)
│
├── data/
│   └── generate_sample.py          ← Synthetic dataset generator
│
├── dataset/
│   └── creditcard.csv              ← Kaggle credit card fraud dataset
│
├── reports/                        ← Auto-generated CSV/audit reports
│   └── logs/
│       └── system.log              ← Rotating JSON application log
│
├── requirements.txt                ← Python dependencies
├── Dockerfile                      ← Streamlit container
├── Dockerfile.api                  ← FastAPI container
└── docker-compose.yml              ← Full stack compose
```

---

## ⚡ Quick Start (Local)

### Prerequisites
- Python 3.10+
- pip

### 1 — Install Dependencies

```bash
cd "d:\Vinayak_IT_Internship\Month3\Task4"
pip install -r requirements.txt
```

### 2 — (Optional) Train the ML Model

```bash
# Trains XGBoost on creditcard.csv and saves backend/model/fraud_model.pkl
python -m backend.model.train_model
```
> The model auto-trains on first API request if the pickle doesn't exist.

### 3 — Launch the Dashboard

```bash
streamlit run app.py
```
Open your browser at **http://localhost:8501**

### 4 — (Optional) Launch the FastAPI Backend

```bash
uvicorn backend.app_api:app --reload --port 8000
```
- Swagger UI: **http://localhost:8000/docs**
- ReDoc:       **http://localhost:8000/redoc**

---

## 🐳 Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Dashboard → http://localhost:8501
# API       → http://localhost:8000/docs
```

To enable PostgreSQL, uncomment the `postgres` section in `docker-compose.yml`.

---

## 🔌 API Reference

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/auth/token` | Get JWT token | No |
| `POST` | `/predict` | Fraud prediction | No* |
| `GET`  | `/predict/health` | Model status | No |
| `GET`  | `/alerts` | List all alerts | JWT |
| `POST` | `/alerts` | Create alert | JWT |
| `PATCH`| `/alerts/{id}` | Update alert | JWT |
| `GET`  | `/alerts/summary` | Alert stats | JWT |
| `POST` | `/cases` | Open case | JWT |
| `GET`  | `/cases` | List cases | JWT |
| `PATCH`| `/cases/{id}` | Update case | JWT |
| `POST` | `/cases/{id}/notes` | Add note | JWT |
| `GET`  | `/health` | System health | No |
| `GET`  | `/metrics` | Operational metrics | No |

### Example: Predict Fraud

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "txn_id": "TXN_123456",
    "card_id": "CARD_9999",
    "Amount": 1250.00,
    "V14": -4.5,
    "V12": -3.2,
    "is_night": 1
  }'
```

**Response:**
```json
{
  "txn_id": "TXN_123456",
  "fraud_probability": 0.9124,
  "risk_score": 91.24,
  "decision": "Fraud",
  "risk_level": "CRITICAL",
  "confidence": 0.8248,
  "timestamp": "2026-05-05T18:00:00Z"
}
```

### Example: Get JWT Token

```bash
curl -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=secret"
```

---

## 📊 Dashboard Pages

| Page | Icon | Description |
|------|------|-------------|
| **Main Dashboard** | 🛡️ | Live transaction feed, KPI cards, risk charts, suspicious accounts |
| **Alert Management** | 🚨 | Filter, triage, assign investigators, create cases |
| **Business Metrics** | 📈 | ROI, precision/recall/F1, savings breakdown, 7-day trends |
| **Compliance** | 📝 | SHAP explainability, audit trail, CSV/TXT report download |
| **Fraud Patterns** | 🔍 | High-freq accounts, amount anomalies, geo & time-of-day analysis |
| **Investigation** | 🗂️ | Case kanban board, notes, investigator workload chart |

---

## 🤖 Machine Learning Pipeline

| Step | Details |
|------|---------|
| **Dataset** | Kaggle Credit Card Fraud (284,807 txns, 0.17% fraud) |
| **Features** | V1–V28 (PCA), Amount, Time + engineered (is_night, Amount_log, Amount_sq) |
| **Balancing** | SMOTE oversampling on training set only |
| **Model** | XGBoost (primary) / Random Forest (fallback) |
| **Evaluation** | ROC-AUC ≈ 0.98, Avg Precision ≈ 0.87 |
| **Explainability** | SHAP-like feature contributions per transaction |

---

## 🔐 Security

- **JWT Authentication** via `python-jose` + `bcrypt`
- **Input Validation** via Pydantic v2 models
- **Structured Logging** with rotating JSON log files
- **No raw card data stored** — only masked IDs
- **Audit trail** for all analyst actions

---

## ☁️ Cloud Deployment

| Component | Recommended Platform |
|-----------|---------------------|
| Streamlit Dashboard | **Streamlit Community Cloud** (free) |
| FastAPI Backend | **Render** or **Railway** |
| PostgreSQL | **Supabase** or **Railway Postgres** |
| Model Storage | **AWS S3** or **GCS** |

### Streamlit Cloud
1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Point to `app.py` as the main file
4. Add secrets via the Streamlit Secrets panel

### Render (FastAPI)
1. Create a new **Web Service**
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn backend.app_api:app --host 0.0.0.0 --port $PORT`

---

## 📋 Business Metrics Explained

| Metric | Formula |
|--------|---------|
| **ROI** | `(Fraud Prevented + Chargebacks Saved − System Cost) / System Cost` |
| **Precision** | `TP / (TP + FP)` |
| **Recall** | `TP / (TP + FN)` |
| **F1 Score** | `2 × Precision × Recall / (Precision + Recall)` |
| **False Positive Rate** | `FP / (FP + TN)` |

---

## 📜 Regulatory Compliance

| Regulation | Coverage |
|-----------|---------|
| **GDPR Art. 22** | SHAP explainability per transaction |
| **Fair Credit Reporting Act** | Adverse action reasoning |
| **SR 11-7** | Model risk management documentation |
| **PCI-DSS** | No raw card data stored |

---

## 👤 Author

**Vinayak IT Internship — Month 3, Task 4**
Built as a complete, production-ready fraud monitoring product demonstrating:
- Real-time ML inference pipeline
- Enterprise dashboard with 5 functional modules
- REST API with JWT security
- Full compliance and audit infrastructure

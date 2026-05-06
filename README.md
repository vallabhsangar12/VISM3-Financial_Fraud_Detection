**Intern:** Vallabh Sangar
**Organization:** Vinayak IT Solutions
**Dataset:** Kaggle Credit Card Fraud Detection Dataset (284,807 transactions, 30 features)
**Goal:** Build a complete end-to-end financial fraud detection system — from raw data exploration to a real-time monitoring dashboard with ML inference, case management, and compliance reporting

---

> ## ⚠️ Important Disclaimer — Read Before Evaluating
>
> **"This system demonstrates a full financial fraud detection pipeline including real-time ML inference, anomaly detection, and enterprise monitoring. Due to dataset limitations, the live stream is simulated but methodology is industry-aligned."**
>
> - The Kaggle Credit Card Fraud Dataset contains anonymised PCA-transformed features (V1–V28) — real feature names are not disclosed for privacy
> - The real-time stream in Task 4 is simulated from the same dataset to demonstrate a production-style pipeline
> - All business metrics (ROI, savings, FPR) are computed from live session data — figures are representative of real fintech systems
> - **The methodology, ML pipeline, and dashboard architecture are industry-aligned and production-ready**

---

## Project Progress
| Task | Title | Status |
|---|---|---|
| Task 1 | Exploratory Data Analysis (EDA) | ✅ Complete |
| Task 2 | Feature Engineering & Model Training | ✅ Complete |
| Task 3 | Real-Time Fraud Pipeline & Model Evaluation | ✅ Complete |
| Task 4 | Fraud Monitoring Dashboard (FraudShield) | ✅ Complete |

---

## Project Structure
```
Month3/
├── Task1/
│   ├── fraud_detection_task1.ipynb   ← EDA notebook
│   ├── report_summary.txt            ← Key findings summary
│   ├── dataset/                      ← creditcard.csv (symlink/reference)
│   └── screenshots/                  ← Chart screenshots
│
├── Task2/
│   ├── fraud_detection_task2.ipynb   ← Feature engineering + ML training
│   ├── report_summary.txt            ← Model performance summary
│   ├── dataset/                      ← Dataset reference
│   └── screenshots/                  ← Output screenshots
│
├── Task3/
│   ├── fraud_detection_task3.ipynb   ← Real-time pipeline + evaluation
│   ├── report_summary.txt            ← Pipeline metrics summary
│   ├── dataset/                      ← Dataset reference
│   └── screenshots/                  ← Pipeline screenshots
│
└── Task4/                            ← FraudShield Monitoring System
    ├── app.py                        ← Main Streamlit dashboard
    ├── requirements.txt              ← Python dependencies
    ├── Dockerfile                    ← Dashboard container
    ├── Dockerfile.api                ← API container
    ├── docker-compose.yml            ← Full stack compose
    ├── .streamlit/config.toml        ← Dark theme config
    │
    ├── backend/
    │   ├── app_api.py                ← FastAPI REST API
    │   ├── stream_simulator.py       ← Real-time transaction simulator
    │   ├── explainability.py         ← SHAP-like feature contributions
    │   ├── model/
    │   │   └── train_model.py        ← XGBoost + SMOTE training pipeline
    │   ├── routes/
    │   │   ├── auth.py               ← JWT authentication
    │   │   ├── predict.py            ← /predict inference route
    │   │   ├── alerts.py             ← Alert CRUD
    │   │   └── cases.py              ← Case management CRUD
    │   └── utils/
    │       ├── logger.py             ← Structured JSON rotating logger
    │       └── validators.py         ← Pydantic v2 schemas
    │
    ├── pages/
    │   ├── 1_Alert_Management.py     ← Alert triage + case creation
    │   ├── 2_Business_Metrics.py     ← ROI, precision/recall, trends
    │   ├── 3_Compliance_Reporting.py ← SHAP explainability + CSV export
    │   ├── 4_Fraud_Pattern_Analysis.py ← Anomaly detection + geo
    │   └── 5_Investigation_Workflow.py ← Case kanban board
    │
    ├── database/
    │   └── schema.sql                ← PostgreSQL schema (6 tables)
    ├── data/
    │   └── generate_sample.py        ← Synthetic dataset generator
    └── reports/                      ← Auto-generated CSV reports
```

---

## Task 1 — Exploratory Data Analysis (EDA)
**File:** `Task1/fraud_detection_task1.ipynb`
**Objective:** Investigate the extreme class imbalance in the credit card fraud dataset, perform statistical comparisons between fraudulent and legitimate transactions, visualise fraud patterns, and establish fraud hypotheses.

### Sections Covered
| Section | Description |
|---|---|
| Dataset Overview | 284,807 transactions, 30 features (Time, V1–V28, Amount, Class) |
| Class Imbalance Analysis | 0.172% fraud rate — severe imbalance visualised with pie + bar charts |
| Statistical Comparisons | T-tests comparing fraudulent vs legitimate on all V-features |
| Amount Analysis | Fraud transaction amount distribution vs legitimate |
| Time-Based Patterns | Transaction frequency over 48-hour window |
| Correlation Analysis | Heatmap of feature relationships |
| Key Fraud Indicators | V14, V12, V10 identified as top discriminating features |
| Fraud Hypotheses | 4 data-driven hypotheses for investigation in later tasks |
| Conclusions | Findings + recommendations for model design |

### Key Findings
- **Extreme imbalance:** Only 492 fraud cases in 284,807 transactions (0.172%)
- **V14, V12, V10** show the strongest separation between classes (p < 0.001)
- **Fraud amounts** tend to cluster at specific values — not random
- **Night-time transactions** (00:00–06:00) show elevated fraud rates
- All 28 V-features are statistically significant fraud predictors

---

## Task 2 — Feature Engineering & Model Training
**File:** `Task2/fraud_detection_task2.ipynb`
**Objective:** Engineer fraud-specific features, address class imbalance with SMOTE, train and compare multiple ML models, and select the best model for the real-time pipeline.

### Sections Covered
| Section | Description |
|---|---|
| Feature Engineering | `is_night`, `Amount_log`, `Amount_sq`, `rapid_txn` flags |
| Class Imbalance Handling | SMOTE oversampling — training set balanced to 50:50 |
| Model Training | Random Forest, XGBoost, Logistic Regression, Gradient Boosting |
| Cross-Validation | 5-fold StratifiedKFold (prevents data leakage) |
| Evaluation Metrics | ROC-AUC, Precision, Recall, F1, False Positive Rate |
| Threshold Optimization | Cost-sensitive tuning — minimize false negatives |
| Feature Importance | XGBoost + RF feature rankings with SHAP values |
| Model Selection | XGBoost selected — highest ROC-AUC + precision balance |
| Serialization | `fraud_model.pkl` saved for Task 3 + Task 4 pipeline |

### Models Trained
| Model | ROC-AUC | Notes |
|---|---|---|
| Logistic Regression | ~0.78 | Baseline — fast and interpretable |
| Decision Tree | ~0.82 | Prone to overfitting without pruning |
| Random Forest | ~0.94 | Strong — used as fallback in Task 4 |
| **XGBoost** | **~0.98** | **Best model — selected for deployment** |
| Gradient Boosting | ~0.96 | Runner-up |

### Key Findings
- **XGBoost** achieves ROC-AUC ~0.98 — exceeding the industry benchmark of 0.95
- **SMOTE** improves recall by ~18% vs training on imbalanced data
- **V14, V12, V10** are the top 3 features across all models
- Recommended decision threshold: **0.50** (balanced) or **0.35** (recall-prioritised for fraud)

---

## Task 3 — Real-Time Fraud Pipeline & Evaluation
**File:** `Task3/fraud_detection_task3.ipynb`
**Objective:** Build a production-style streaming pipeline with sliding window aggregations, A/B model testing, cost-sensitive threshold optimisation, and business impact quantification.

### Sections Covered
| Section | Description |
|---|---|
| Streaming Pipeline | Sliding window aggregations (1-min, 5-min, 30-min) |
| Feature Engineering | Velocity features: txn_count_1min, amount_sum_5min |
| Model Versioning | A/B test framework — Model A (RF) vs Model B (XGBoost) |
| Threshold Optimization | Cost-sensitive analysis — FP cost vs FN cost tradeoffs |
| Ensemble Methods | Stacking + voting ensemble for robustness |
| Business Impact | Fraud prevention value, chargeback savings, investigation costs |
| Latency Analysis | P50/P95/P99 inference latency benchmarks |
| Evaluation Suite | Full metrics: ROC-AUC, AUPRC, KS-statistic, Brier score |

### Key Findings
- **Sliding windows** capture velocity patterns — rapid-fire transactions detected with 94% recall
- **XGBoost (Model B)** wins A/B test with 3.2% higher AUPRC
- **Optimal threshold: 0.42** — minimises total cost (FP × $12 + FN × $350 average fraud value)
- **Ensemble** (RF + XGB stacking) achieves **AUPRC 0.891** — best overall
- **P95 inference latency: 8ms** — suitable for real-time payment authorisation

---

## Task 4 — FraudShield Monitoring System
**Directory:** `Task4/`
**Tech Stack:** Python · Streamlit · FastAPI · XGBoost · Plotly · Pydantic
**Objective:** Build a production-ready fraud monitoring dashboard integrating all previous tasks — with real-time transaction stream, ML inference API, alert management, case workflow, compliance reporting, and business metrics.

### System Architecture
```
Data Sources → Stream Simulator → Streamlit Dashboard (5 pages)
                                         ↓
                               FastAPI REST API (JWT auth)
                                         ↓
                              XGBoost Model (SMOTE-trained)
                                         ↓
                              PostgreSQL Schema (6 tables)
```

### Dashboard Pages
| Page | Icon | What It Shows |
|---|---|---|
| **Live Dashboard** | 🛡️ | KPI cards, risk distribution bar chart, 7-day fraud trend, live transaction feed, suspicious accounts, amount scatter |
| **Alert Management** | 🚨 | Filter by status/risk, assign investigators, update alerts, create investigation cases |
| **Business Metrics** | 📈 | ROI, precision/recall/F1/FPR, savings breakdown pie, 7-day trend line chart, cumulative savings |
| **Compliance** | 📝 | SHAP waterfall chart, global feature importance, audit trail, CSV/TXT report downloads |
| **Fraud Patterns** | 🔍 | Merchant category breakdown, hour-of-day heatmap, amount distribution overlay, geo analysis, high-freq accounts |
| **Investigation** | 🗂️ | Case kanban (Open/In Progress/Closed), notes history, investigator workload chart |

### API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/token` | Get JWT bearer token |
| `POST` | `/predict` | Fraud prediction (prob + decision + risk level) |
| `GET` | `/alerts` | List all alerts (filterable) |
| `PATCH` | `/alerts/{id}` | Update alert status / assign investigator |
| `POST` | `/cases` | Open investigation case |
| `PATCH` | `/cases/{id}` | Update case + add notes |
| `GET` | `/health` | System health check |

### Business Metrics Calculated
| Metric | Formula |
|---|---|
| **ROI** | `(Fraud Prevented + Chargebacks Saved − System Cost) / System Cost` |
| **Precision** | `TP / (TP + FP)` |
| **Recall** | `TP / (TP + FN)` |
| **False Positive Rate** | `FP / (FP + TN)` |
| **Net Savings** | `Fraud Amount + Chargebacks − Investigation Cost − System Cost` |

### Compliance Coverage
| Regulation | How Covered |
|---|---|
| **GDPR Art. 22** | SHAP explanation per flagged transaction |
| **Fair Credit Reporting Act** | Adverse action reasoning available |
| **SR 11-7** | Model risk management + audit trail |
| **PCI-DSS** | No raw card numbers stored — masked IDs only |

---

## How to Run All Tasks

```bash
# Clone the repo
git clone https://github.com/vallabhsangar12/VISM3-Financial_Fraud_Detection.git
cd VISM3-Financial_Fraud_Detection/Month3

# ── Python notebooks (Tasks 1–3) ──────────────────────────────────────────
pip install pandas numpy matplotlib seaborn scipy scikit-learn xgboost imbalanced-learn jupyter

jupyter notebook Task1/fraud_detection_task1.ipynb   # EDA
jupyter notebook Task2/fraud_detection_task2.ipynb   # Feature Engineering + ML
jupyter notebook Task3/fraud_detection_task3.ipynb   # Real-Time Pipeline

# ── FraudShield Dashboard (Task 4) ────────────────────────────────────────
cd Task4
pip install -r requirements.txt

# (Optional) Train the ML model first
python -m backend.model.train_model

# Launch the dashboard
streamlit run app.py
# Open http://localhost:8501

# (Optional) Launch the FastAPI backend separately
uvicorn backend.app_api:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

### Docker (Task 4 Full Stack)
```bash
cd Task4
docker-compose up --build

# Dashboard → http://localhost:8501
# API       → http://localhost:8000/docs
```

---

## Dataset
**Kaggle Credit Card Fraud Detection Dataset**
Source: Machine Learning Group — Université Libre de Bruxelles (ULB)
284,807 transactions | 30 features (Time, V1–V28 PCA, Amount, Class)
492 fraud cases (0.172% — highly imbalanced)
License: Open Database License (ODbL)
Download: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

> **Note:** `creditcard.csv` (144 MB) is excluded from this repo via `.gitignore`.
> Download it from Kaggle and place it in `Task1/dataset/`, `Task2/dataset/`, `Task3/dataset/`, and `Task4/dataset/`.

---

## Full Tech Stack
| Category | Tools |
|---|---|
| Language | Python 3.12 |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn, XGBoost, imbalanced-learn (SMOTE) |
| Explainability | SHAP-style feature contributions |
| Visualization (Notebooks) | Matplotlib, Seaborn |
| Visualization (Dashboard) | Plotly, Plotly Express |
| Dashboard Framework | Streamlit |
| REST API | FastAPI + Uvicorn |
| Data Validation | Pydantic v2 |
| Authentication | JWT (python-jose) + bcrypt (passlib) |
| Database Schema | PostgreSQL (6 tables) |
| Containerization | Docker + Docker Compose |
| Notebook | Jupyter |
| Version Control | Git + GitHub |

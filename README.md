# Month 3 - Task 1: Financial Fraud Detection Project

## Project Objective
This project analyzes insurance claim records to identify fraud patterns and satisfy internship requirements for Month 3 Task 1. The analysis focuses on imbalanced fraud labels, claim amount behavior, time-based patterns, geographical risk, category-like incident behavior, and statistical differences between fraud and non-fraud claims.

## Dataset Used
- Source file: `dataset/insurance_claims.csv`
- Domain: Auto insurance claim fraud detection
- Target variable: `fraud_reported` (`Y` = fraud, `N` = non-fraud)

## Analysis Performed
1. Dataset understanding and feature review
2. Data cleaning (`?` handling, date conversion, numeric conversion)
3. Fraud indicator analysis across categorical factors
4. Class imbalance analysis (fraud vs non-fraud ratio)
5. Transaction amount distribution by fraud class
6. Time pattern analysis (`incident_hour_of_the_day`)
7. Geographical fraud analysis (state and city level)
8. Merchant/category-like analysis using `incident_type`
9. Statistical comparison (mean, median, std for key numerical features)
10. Fraud prevalence rate calculation
11. Transaction frequency analysis
12. Time series fraud trend analysis (`incident_date` monthly trend)
13. Fraud heatmap (`incident_severity` x `incident_type`)
14. Correlation analysis for fraud-related numeric indicators
15. Initial fraud hypothesis and final pattern summary

## Generated Outputs
### Figures (`outputs/figures/`)
- `class_imbalance.png`
- `amount_distribution.png`
- `fraud_by_hour.png`
- `fraud_by_state.png`
- `fraud_by_city.png`
- `fraud_heatmap.png`
- `merchant_category_analysis.png`
- `correlation_analysis.png`
- `time_series_fraud_trend.png`

### Reports (`outputs/reports/`)
- `class_imbalance.csv`
- `stats_comparison.csv`
- `fraud_prevalence.csv`
- `fraud_patterns_summary.txt`
- `hypothesis.txt`
- `overview.txt`

## Internship Submission Screenshot Checklist
Capture screenshots from notebook outputs for:
1. Class imbalance analysis
2. Fraud pattern visualizations
3. Statistical comparison results
4. Initial fraud hypothesis

## How to Run
```bash
pip install -r requirements.txt
```

Optional notebook workflow:
1. Open `notebooks/task1_fraud_eda.ipynb`
2. Run cells top to bottom
3. Outputs will be saved under `outputs/figures/` and `outputs/reports/`

## Key Findings (High-Level)
- Fraud class is imbalanced versus non-fraud.
- Fraud rates vary by geography and incident type.
- Claim amount and incident-related features show meaningful fraud pattern differences.
- Time-based signals (hourly and monthly) are useful for fraud monitoring.

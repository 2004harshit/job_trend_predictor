# Job Trend Predictor
### Predicting the Trends of Quality Oriented Jobs

> A data-driven career intelligence platform that transforms raw Naukri.com job data into personalized, actionable guidance for students, freshers, and career counselors — built as a B.Tech final year project at SKIT, Jaipur.

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit_Cloud-red?style=flat-square&logo=streamlit)](https://streamlit.io)
[![Flask](https://img.shields.io/badge/Backend-Flask_on_Render-black?style=flat-square&logo=flask)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/Database-MySQL-orange?style=flat-square&logo=mysql)](https://mysql.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**Live Demo:** [job-trend-predictor.streamlit.app](https://job-trend-predictor.streamlit.app) &nbsp;|&nbsp;
**Project ID:** SKIT/CSE/2022-2026/028 &nbsp;|&nbsp;
**Mentor:** Dr. Pankaj Dadheech

---

## The Problem

Students and freshers in India are forced to make critical career decisions based on YouTube opinions, sponsored course advice, and outdated information. LinkedIn and Naukri show *what jobs exist today* — but nobody tells you which domain suits your current skills, what salary you can realistically expect in your city, or how crowded a field actually is for someone just starting out.

Three specific gaps exist in every current platform:

- **The Incentive Gap** — Most career advice online is influenced by course sales, not actual hiring data
- **The Granularity Gap** — Job descriptions say "Python" but don't tell you the level or practical depth required
- **The Lagging Indicator Problem** — By the time a skill becomes popular in courses, job demand may already be declining

**This platform fills that gap** with real job data, honest analytics, and personalized output.

---

## What's Actually Built (Current Version — MVP)

This is an honest description of what is implemented and working:

### Fresher Dashboard — Domain Confusion Resolver
A student enters their experience level, preferred city, current skills (e.g. Python, SQL), and math comfort level. The system:
- Scores compatibility across multiple tech domains using a rule-based engine
- Recommends the best-fit domain with a compatibility percentage
- Shows market reality: hiring pulse score, competition intensity, fresher salary range
- Shows path to entry: time-to-job-ready estimates, prerequisites, interview difficulty score
- Shows long-term growth: salary progression over 0–2 years and 3–5 years
- Shows "Real Talk": the harsh truth about entry-level competition and the silver lining

### Career Counselor Dashboard
A counselor or teacher can view:
- **Live Market Pulse** — total jobs, active domains, top skill, median salary across all listings
- **Domain Comparison** — side-by-side metrics for up to 5 domains, skill cross-overlap heatmap, fresher eligibility percentages, top companies hiring freshers
- **Salary Intelligence** — salary distribution with P25/P75 percentiles, domain and location filters, Jaipur vs National comparison
- **Skill Gap Analyzer** — in development
- **Company Intelligence** — in development

### What's Not Yet Built (Honest)
- No ML model for prediction — analytics are rule-based calculations on the dataset
- No real-time scraping — data is a Dec 2025–Feb 2026 snapshot (11,000+ listings)
- No user login or profile saving
- Skill Gap Analyzer and Upskilling Advisor modules are in development

---

## Architecture

The system follows a three-tier decoupled architecture deployed across two cloud platforms:

```
┌─────────────────────────────────────────────────────────┐
│  User (Browser)                                         │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP
┌───────────────────▼─────────────────────────────────────┐
│  Presentation Layer — Streamlit (Streamlit Cloud)       │
│  Landing Page → Persona Selection → Dashboard           │
│  Interactive charts, filters, domain comparison UI      │
└───────────────────┬─────────────────────────────────────┘
                    │ REST API calls
┌───────────────────▼─────────────────────────────────────┐
│  Application Layer — Flask API (Render)                 │
│  Analytics Engine: domain analysis, market analysis,   │
│  entry barriers, career insights, recommendation engine │
│  7 endpoints: /health, /domains, /recommend,            │
│  /domain-analysis, /domain-compare, /market, /stats    │
└───────────────────┬─────────────────────────────────────┘
                    │ Query
┌───────────────────▼─────────────────────────────────────┐
│  Data Layer — MySQL + CSV (Cloud Storage)               │
│  raw_job_data table — 11,000+ cleaned job listings     │
│  Scraped from Naukri.com, Dec 2025 – Feb 2026          │
└─────────────────────────────────────────────────────────┘
```

The frontend and backend are independently deployable — updating one does not affect the other.

---

## Data Pipeline

Raw data goes through five sequential stages before reaching the dashboard:

```
Naukri.com
    │
    ▼
[1] Scraping Pipeline
    NaukriFresherJobScraper  (0-2 yrs experience)
    NaukriGeneralJobScraper  (all experience levels)
    Dual storage → CSV (raw/) + MySQL
    │
    ▼
[2] 17-Strategy Cleaning Pipeline
    Missing value handling → Duplicate removal →
    Salary parsing & standardization → Skills extraction →
    Location normalization → Quality validation →
    Output: data/processed/ + data/rejected/
    │
    ▼
[3] Analytics Engine
    DomainAnalytics → MarketAnalysis → EntryBarriers →
    CareerInsights → RealTalkEngine → DomainRecommender
    │
    ▼
[4] Flask REST API
    Structured JSON responses → Streamlit frontend
    │
    ▼
[5] Streamlit Dashboard
    Interactive charts, personalized output
```

---

## Object-Oriented Design Patterns Used

| Pattern | Where Applied |
|---|---|
| **Strategy Pattern** | 17 cleaning strategies — each is a separate, swappable class |
| **Template Method** | Base scraper defines the pipeline; subclasses implement platform-specific extraction |
| **Abstract Class / Open-Closed Principle** | `JobExtractor` and `StorageHandler` abstract classes — new platforms added without modifying existing code |
| **Facade Pattern** | `AnalyticsPipeline` orchestrates all engine modules behind a single interface |
| **Dependency Injection** | Recommendation engine accepts mocked sub-engines for unit testing |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Frontend | Streamlit |
| Backend API | Flask |
| Database | MySQL, CSV files |
| Scraping | Selenium, BeautifulSoup, Requests |
| Data Processing | Pandas, NumPy |
| Charts | Plotly |
| Testing | PyTest |
| Config Management | PyYAML |
| Version Control | GitHub |
| Frontend Deployment | Streamlit Cloud |
| Backend Deployment | Render |

---

## Project Structure

```
job_trend_predictor/
├── app.py                          # Streamlit entry point
├── run_pipeline.py                 # Pipeline orchestrator
├── requirements.txt
├── .env.example
├── config/
│   ├── config.yml                  # Scraping & pipeline settings
│   ├── logging.yml
│   └── cleaning_config.json
├── src/
│   ├── scrapers/                   # NaukriFresherJobScraper, NaukriGeneralJobScraper
│   ├── cleaners/                   # 17 cleaning strategy classes
│   ├── storage/                    # CSVStorageHandler, SQLStorageHandler
│   ├── validators/                 # Data quality checks
│   ├── analytics/
│   │   ├── domain_analysis/        # Hiring frequency, competition scoring
│   │   ├── market_analysis/        # Demand scoring, salary distribution
│   │   ├── entry_barriers/         # Interview difficulty, prerequisites
│   │   ├── career_insights/        # Career growth, salary progression
│   │   └── real_talk/              # Harsh truth engine
│   ├── recommender/                # Rule-based domain scoring engine
│   └── api/                        # Flask REST API endpoints
├── dashboards/
│   ├── pages/
│   │   ├── landing.py
│   │   ├── persona_selection.py
│   │   ├── fresher_dashboard.py    # Domain Confusion Resolver
│   │   └── counselor_dashboard.py
│   └── components/                 # Reusable Streamlit components
├── pipelines/
│   ├── fresher_pipeline.py
│   ├── general_pipeline.py
│   └── cleaning_pipeline.py
├── data/
│   ├── raw/                        # Freshly scraped data
│   └── processed/                  # Cleaned, validated data
├── tests/
│   ├── test_scrapers.py
│   ├── test_cleaners.py
│   ├── test_storage.py
│   ├── test_recommender.py
│   ├── test_api.py
│   └── evaluation_metrics.py
├── notebooks/                      # EDA and experimentation
└── logs/
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- MySQL Server (optional — CSV mode works without it)
- Chrome/Chromium (for Selenium scraping)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/2004harshit/job_trend_predictor
cd job_trend_predictor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 4. (Optional) Initialize MySQL database
mysql -u root -p < scripts/init_database.sql
```

### Run the Dashboard

```bash
streamlit run app.py
```

The Streamlit app connects to the deployed Flask backend on Render by default. No local backend setup needed to use the dashboard.

### Run the Data Pipeline

```bash
# Scrape fresher jobs (0-2 years experience)
python run_pipeline.py --mode fresher

# Scrape all job levels
python run_pipeline.py --mode general

# Run both
python run_pipeline.py --mode all
```

### Run the Flask Backend Locally

```bash
cd src/api
flask run --port 5000
```

Update `FLASK_API_URL` in your `.env` to point to `http://localhost:5000` if running locally.

---

## Configuration

### Environment Variables (`.env`)

```env
# Flask API endpoint
FLASK_API_URL=https://your-render-app.onrender.com

# Database (optional — CSV mode works without this)
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=job_trends
```

### Pipeline Configuration (`config/config.yml`)

```yaml
pipeline:
  max_pages: 10
  per_page_limit: 15
  min_delay: 3        # seconds between requests
  max_delay: 7
  timeout: 30
  max_retries: 3

fresher_pipeline:
  max_pages: 5
  per_page_limit: 20
  min_delay: 2
  max_delay: 5
```

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific module
python -m pytest tests/test_cleaners.py -v

# Run with coverage
python -m pytest --cov=src tests/

# Run API endpoint tests
python tests/test_api.py

# Evaluate recommendation engine (30 synthetic profiles)
python tests/evaluation_metrics.py
```

### Test Coverage Summary

| Module | Tests | Key Scenarios |
|---|---|---|
| Scraping Pipeline | 8 | Abstract enforcement, edge cases, mock HTML |
| Cleaning Pipeline | 8 | Valid/invalid inputs, salary parsing, skill extraction |
| Storage Handlers | 8 | CSV, JSON, SQLite — valid data, empty data, invalid paths |
| Recommendation Engine | 8 | Skill scoring, math penalty, feasibility, sorting |

Recommendation engine evaluation uses **Precision@3**, **Hit Rate**, and **NDCG@3** metrics across 30 synthetic user profiles.

---

## Dataset

| Property | Detail |
|---|---|
| Source | Naukri.com |
| Collection period | December 2025 – February 2026 |
| Total listings | ~11,000+ after cleaning |
| Geography | Jaipur, Bangalore, Delhi, Mumbai, Hyderabad, Pune |
| Experience range | Fresher (0–2 yrs) + General (all levels) |
| Fields captured | Title, company, salary, location, skills, experience, job URL |

> **Note on salary data:** ~60% of Naukri listings mark salary as "Not Disclosed". All salary figures are estimates derived from the disclosed subset only. This limitation is shown transparently in the dashboard.

---

## Agile Development — Sprint Summary

| Sprint | Deliverable | Status |
|---|---|---|
| Sprint 1 | Data Scraping Pipeline (Naukri, dual storage) | ✅ Done |
| Sprint 2 | 17-Strategy Data Cleaning Pipeline | ✅ Done |
| Sprint 3 | Analytics Engine + Flask REST API | ✅ Done |
| Sprint 4 | Streamlit Frontend + Domain Confusion Resolver | ✅ Done |
| Sprint 5 | Integration, cloud deployment, end-to-end testing | ✅ Done |

---

## Team

| Member | Roll No. | Module |
|---|---|---|
| Harsh | 22ESKCS094 | Frontend (Streamlit), integration, deployment |
| Harsh Dhakad | 22ESKCS095 | Data scraping pipeline, raw storage |
| Gulshan Kumar | 22ESKCS092 | 17-strategy data cleaning pipeline |
| Harshit Chauhan | 22ESKCS098 | Analytics engine, Flask REST API, recommender |

**Mentor:** Dr. Pankaj Dadheech, Professor, CSE — SKIT, Jaipur  
**Coordinator:** Mr. Sumit Mathur, Assistant Professor, CSE — SKIT, Jaipur

---

## UN Sustainable Development Goals

This project contributes to three SDGs under the UN 2030 Agenda:

- **SDG 4 — Quality Education:** Helps students and institutions align learning with actual industry demand
- **SDG 8 — Decent Work and Economic Growth:** Reduces skill-employment mismatch, improves fresher employability
- **SDG 9 — Industry, Innovation and Infrastructure:** Brings real industry data into education through an innovative analytics platform

---

## Future Scope

- **Automatic data refresh** — scheduled scraping pipeline replacing manual runs
- **Skill Gap Analyzer** — enter current skills, get exact gap against role requirements with a learning roadmap
- **More data sources** — LinkedIn, Indeed, company career pages
- **ML forecasting** — ARIMA/Prophet models for 6–12 month demand prediction
- **User accounts** — save profiles, track progress, get notifications
- **Mobile app** — Android/iOS for on-the-go career insights

---

## Academic Details

| Field | Detail |
|---|---|
| Institution | Swami Keshvanand Institute of Technology, M & G, Jaipur |
| University | Rajasthan Technical University, Kota |
| Department | Computer Science and Engineering |
| Degree | Bachelor of Technology (B.Tech) |
| Project ID | SKIT/CSE/2022-2026/028 |
| Session | 2025–2026 |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

*Built with honesty and real data*
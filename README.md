# 🧠 Job Market Intelligence System

A comprehensive Data + ML + LLM powered platform that analyzes and predicts job market trends for students, policy-makers, and career counselors.

## 📋 Table of Contents

- [🌍 Project Overview](#-project-overview)
- [🎯 Core Objectives](#-core-objectives)
- [👥 Target Audience & Deliverables](#-target-audience--deliverables)
- [⚙️ System Architecture](#️-system-architecture)
- [🔧 Technology Stack](#-technology-stack)
- [📁 Project Structure](#-project-structure)
- [🚀 Quick Start](#-quick-start)
- [🔧 Configuration](#-configuration)
- [📊 Features](#-features)
- [🧪 Testing](#-testing)
- [🚀 Deployment](#-deployment)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🌍 Project Overview

The Job Market Intelligence System is an AI-powered decision-support tool designed to analyze real-time job postings and uncover emerging patterns in hiring, salary, and skill demand. It serves three key stakeholders:

- **Students/Freshers**: Make informed career decisions with data-driven insights
- **Career Counselors**: Guide students with market-aligned recommendations
- **Policy-Makers**: Design curriculum and placement strategies based on evidence

The system combines Machine Learning predictions with LLM-generated insights to provide both quantitative analysis and qualitative explanations of job market trends.

---

## 🎯 Core Objectives

- **Trend Identification**: Identify current trends in demand, location, skill importance, and salary variations
- **Predictive Analytics**: Predict salary and job type based on skills and experience level
- **Explainable Insights**: Provide LLM-powered insights explaining why certain roles or skills are trending
- **Interactive Visualization**: Display findings in a dynamic BI dashboard for data-driven decisions
- **Future Forecasting**: Forecast job trends using time-series and NLP techniques (next semester goal)

---

## 👥 Target Audience & Deliverables

| Target Group | Needs / Problem | System Deliverables |
|--------------|-----------------|-------------------|
| **Students / Freshers** | Unaware of which skills or domains offer job opportunities & better pay | Skill-based salary prediction, demand analysis, and personalized insights |
| **Career Counselors / Placement Officers** | Need data to guide students toward employable skillsets | BI Dashboard with skill-demand trends, hiring ratios, and salary statistics |
| **Policy-Makers / Institutions** | Need evidence to design curriculum and placement strategy | Aggregate hiring insights, fresher demand ratio, and regional/sectoral trends |

---

## ⚙️ System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Data Pipeline   │───▶│   Analytics     │
│                 │    │                  │    │                 │
│ • Naukri.com    │    │ • Scraping       │    │ • ML Models     │
│ • LinkedIn      │    │ • Cleaning       │    │ • LLM Insights  │
│ • Other Portals │    │ • Processing     │    │ • Analytics     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐            ▼
│   Users         │◀───│   BI Dashboard    │    ┌─────────────────┐
│                 │    │                  │    │   Storage       │
│ • Students      │    │ • Streamlit App  │    │                 │
│ • Counselors    │    │ • Interactive    │    │ • MySQL         │
│ • Policy Makers │    │ • Visualizations │    │ • CSV Files     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

#### 1. **Data Collection Layer**
- **Web Scrapers**: Selenium-based scrapers for Naukri.com and other job portals
- **Data Extractors**: Structured extraction of job titles, skills, salary, location, etc.
- **Rate Limiting**: Configurable delays and retry mechanisms

#### 2. **Data Processing Pipeline**
- **Cleaning Module**: Remove duplicates, handle missing values, normalize currencies
- **Feature Engineering**: Extract skill keywords, encode experience levels, NLP processing
- **Validation**: Data quality checks and validation rules

#### 3. **Analytics Engine**
- **Career Insights**: Career path analysis, role evaluation
- **Domain Analysis**: AI replacement risk, domain stability, salary growth
- **Market Analysis**: Demand scoring, competition levels, salary calculations
- **Entry Barriers**: Interview difficulty, prerequisite analysis, project complexity

#### 4. **Machine Learning Layer**
- **Salary Prediction**: Regression models for salary estimation
- **Job Type Classification**: Categorize full-time, internship, contract roles
- **Skill Demand Analysis**: Track trending skills and their market value

#### 5. **LLM Insight Layer**
- **Trend Summarization**: Generate human-readable explanations of trends
- **Contextual Insights**: Explain why certain roles or skills are trending
- **Recommendation Engine**: Provide personalized career guidance

#### 6. **Visualization Dashboard**
- **Multi-User Interface**: Different views for students, counselors, and policymakers
- **Interactive Charts**: Skill vs salary, experience trends, location heatmaps
- **Real-time Updates**: Dynamic data refresh and filtering

---

## 🔧 Technology Stack

### Data Layer
- **Storage**: MySQL, CSV files
- **Processing**: Pandas, NumPy
- **Web Scraping**: Selenium, BeautifulSoup, Requests

### Analytics & ML
- **Machine Learning**: Scikit-learn (Linear Regression, RandomForest, XGBoost)
- **NLP**: spaCy, NLTK, TF-IDF
- **LLM Integration**: OpenAI API / LlamaIndex (planned)

### Frontend & Visualization
- **Dashboard**: Streamlit
- **Styling**: Custom CSS, Tailwind CSS
- **Charts**: Plotly, Streamlit components

### Infrastructure & DevOps
- **Configuration**: YAML, Environment variables
- **Logging**: Python logging, custom session loggers
- **Testing**: Unit tests (pytest framework)
- **MLOps (Future)**: MLflow, ZenML, Git

---

## 📁 Project Structure

```
job_trend_predictor/
├── 📄 app.py                          # Main Streamlit application
├── 📄 run_pipeline.py                 # Pipeline orchestrator
├── 📄 .env                            # Environment variables
├── 📁 config/                         # Configuration files
│   ├── 📄 config.yml                  # Main pipeline configuration
│   ├── 📄 logging.yml                 # Logging configuration
│   └── 📄 cleaning_config.json        # Data cleaning settings
├── 📁 src/                            # Core source code
│   ├── 📁 analytics/                  # Analytics engines
│   │   ├── 📁 career_insights/        # Career path analysis
│   │   ├── 📁 domain_analysis/        # Domain-specific analysis
│   │   ├── 📁 entry_barriers/         # Entry barrier analysis
│   │   └── 📁 market_analysis/        # Market trend analysis
│   ├── 📁 scrapers/                   # Web scraping modules
│   ├── 📁 storage/                    # Data storage handlers
│   ├── 📁 cleaners/                   # Data cleaning modules
│   ├── 📁 models/                     # ML models
│   ├── 📁 utils/                      # Utility functions
│   └── 📁 validators/                 # Data validation
├── 📁 dashboards/                     # Streamlit dashboard
│   ├── 📁 pages/                      # Dashboard pages
│   ├── 📁 components/                 # Reusable components
│   └── 📁 utils/                      # Dashboard utilities
├── 📁 pipelines/                      # ETL pipelines
├── 📁 notebooks/                      # Jupyter notebooks
├── 📁 tests/                          # Unit tests
├── 📁 data/                           # Data files
├── 📁 logs/                           # Log files
└── 📁 models/                         # Trained model files
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MySQL Server (optional, for database storage)
- Chrome/Chromium browser (for Selenium)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd job_trend_predictor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize database (if using MySQL)**
   ```bash
   mysql -u root -p < scripts/init_database.sql
   ```

### Running the Application

#### Option 1: Run the Dashboard
```bash
streamlit run app.py
```

#### Option 2: Run Data Pipeline
```bash
# Run fresher job scraping
python run_pipeline.py --mode fresher

# Run general job scraping
python run_pipeline.py --mode general

# Run both pipelines
python run_pipeline.py --mode all
```

---

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```env
# Database Configuration
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=job_trends

# API Keys (optional)
OPENAI_API_KEY=your_openai_key
SERP_API_KEY=your_serp_api_key
```

### Pipeline Configuration

Main configuration in `config/config.yml`:

```yaml
pipeline:
  max_pages: 10
  per_page_limit: 15
  min_delay: 3
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

## 📊 Features

### 🎯 Multi-User Dashboard

- **Student Dashboard**: Personalized career insights, skill recommendations, salary predictions
- **Counselor Dashboard**: Aggregate trends, student guidance tools, market analytics
- **Professional Dashboard**: Advanced analytics, role comparisons, market insights

### 🤖 Analytics Capabilities

- **Career Path Analysis**: Skill progression timelines, learning path recommendations
- **Domain Stability**: Market volatility analysis, future-proof career suggestions
- **Salary Insights**: Real-time salary benchmarks, growth projections
- **Entry Barrier Assessment**: Interview difficulty, prerequisite requirements

### 📈 Predictive Models

- **Salary Prediction**: ML-based salary estimation based on skills and experience
- **Job Type Classification**: Automatic categorization of job postings
- **Demand Scoring**: Real-time calculation of skill and role demand

### 🔍 Data Sources

- **Naukri.com**: Comprehensive job listings across India
- **Location Coverage**: Major tech hubs (Delhi, Bengaluru, Mumbai, Hyderabad, Pune, Kolkata)
- **Role Coverage**: Tech roles (Data Scientist, ML Engineer, Software Engineer, DevOps, etc.)

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_analytics.py

# Run with coverage
python -m pytest --cov=src tests/
```

### Test Structure

- **Unit Tests**: Individual component testing
- **Integration Tests**: Pipeline and workflow testing
- **Performance Tests**: Scraping rate limiting and efficiency

---

## 🚀 Deployment

### Local Development

```bash
# Start the dashboard
streamlit run app.py --server.port 8501

# Run pipeline in background
python run_pipeline.py --mode all &
```

### Production Deployment (Planned)

- **Containerization**: Docker support
- **Cloud Deployment**: AWS/GCP/Azure
- **CI/CD Pipeline**: Automated testing and deployment
- **Monitoring**: Application performance and error tracking

---

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make changes and add tests**
4. **Run tests**: `python -m pytest`
5. **Commit changes**: `git commit -m "Add new feature"`
6. **Push to branch**: `git push origin feature/new-feature`
7. **Create Pull Request**

### Code Style

- **Python**: PEP 8 compliance
- **Documentation**: Docstrings for all functions and classes
- **Type Hints**: Use type hints where applicable
- **Testing**: Maintain test coverage > 80%

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔮 Future Roadmap

### Phase 2 - Next Semester

- **Time-Series Forecasting**: Predict future job trends using ARIMA, Prophet, LSTM
- **Skill Evolution Tracking**: Monitor skill demand changes over time
- **Advanced LLM Integration**: Enhanced insights and recommendations
- **MLOps Pipeline**: MLflow integration for model versioning and deployment
- **Public Deployment**: Cloud-hosted Streamlit application

### Long-term Vision

- **Multi-Country Support**: Expand beyond Indian job market
- **Additional Data Sources**: LinkedIn, Indeed, company career pages
- **Mobile Application**: Native mobile app for on-the-go insights
- **API Integration**: RESTful API for third-party integrations
- **Enterprise Features**: Team collaboration, advanced analytics

---

## 📞 Support

For questions, issues, or contributions:

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: your-email@example.com

---

**Built with ❤️ for the next generation of tech professionals**

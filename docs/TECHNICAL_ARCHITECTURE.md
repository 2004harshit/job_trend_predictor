# Technical Architecture Documentation

## 📋 Table of Contents

- [🏗️ System Overview](#️-system-overview)
- [🔧 Component Architecture](#-component-architecture)
- [📊 Data Flow Architecture](#-data-flow-architecture)
- [🤖 Machine Learning Pipeline](#-machine-learning-pipeline)
- [🎯 Analytics Engine Architecture](#-analytics-engine-architecture)
- [🖥️ Dashboard Architecture](#️-dashboard-architecture)
- [🗄️ Data Storage Architecture](#️-data-storage-architecture)
- [🔐 Security & Performance](#-security--performance)
- [🚀 Deployment Architecture](#-deployment-architecture)

---

## 🏗️ System Overview

The Job Market Intelligence System follows a **layered microservices architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Streamlit App  │  │  REST API      │  │  CLI Tools   │ │
│  │  (Dashboard)    │  │  (Future)      │  │  (Pipelines) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Analytics      │  │  ML Models      │  │  LLM Engine  │ │
│  │  Engines        │  │  (Prediction)   │  │  (Insights)  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    Data Processing Layer                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Data Scrapers  │  │  Data Cleaners  │  │  Validators   │ │
│  │  (Collection)   │  │  (Processing)   │  │  (Quality)    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                     Data Access Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Storage        │  │  Cache Layer    │  │  Config      │ │
│  │  (MySQL/CSV)    │  │  (Future)       │  │  (YAML/ENV)  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Architectural Principles

1. **Modularity**: Each component has a single responsibility
2. **Scalability**: Components can be scaled independently
3. **Testability**: Clear interfaces enable comprehensive testing
4. **Maintainability**: Well-structured code with proper documentation
5. **Extensibility**: Easy to add new features and data sources

---

## 🔧 Component Architecture

### 1. Data Collection Components

#### Web Scrapers (`src/scrapers/`)

```python
# Base scraper interface
class JobExtractor(ABC):
    @abstractmethod
    def extract_jobs(self, config: dict) -> List[JobPosting]
    
    @abstractmethod
    def validate_extraction(self, jobs: List[JobPosting]) -> bool
```

**Key Components:**
- **`GeneralJobScraper`**: Scrapes general job postings from Naukri.com
- **`FresherJobScraper`**: Specialized scraper for entry-level positions
- **`BaseScraper`**: Abstract base class with common functionality

**Features:**
- Rate limiting with exponential backoff
- Retry mechanisms for failed requests
- Location-based filtering
- Configurable scraping limits

#### Data Validators (`src/validators/`)

```python
class DataValidator:
    def validate_job_posting(self, job: JobPosting) -> ValidationResult
    def validate_salary_range(self, salary: SalaryInfo) -> bool
    def validate_skills(self, skills: List[str]) -> List[str]
```

### 2. Data Processing Components

#### Data Cleaners (`src/cleaners/`)

**Key Modules:**
- **`SalaryCleaner`**: Normalizes salary formats and currencies
- **`SkillCleaner`**: Standardizes skill terminology
- **`LocationCleaner`**: Normalizes location names
- **`ExperienceCleaner`**: Standardizes experience levels

#### Feature Engineering (`src/preprocessing/`)

```python
class FeatureEngineer:
    def extract_skill_features(self, text: str) -> Dict[str, float]
    def encode_experience_level(self, exp: str) -> int
    def create_salary_buckets(self, salary: float) -> str
```

### 3. Analytics Engine Components

#### Career Insights (`src/analytics/career_insights/`)

**`CareerPathEngine`**
```python
class CareerPathEngine:
    def calculate_learning_path(self, current_skills: List[str], 
                              target_role: str) -> LearningPath
    def estimate_time_to_role(self, path: LearningPath) -> int
    def suggest_skill_priorities(self, role: str) -> List[SkillPriority]
```

**`RoleEvaluationEngine`**
```python
class RoleEvaluationEngine:
    def evaluate_role_fit(self, profile: UserProfile, role: str) -> FitScore
    def compare_roles(self, profile: UserProfile, 
                      roles: List[str]) -> RoleComparison
```

#### Domain Analysis (`src/analytics/domain_analysis/`)

**`AIReplacementRiskEngine`**
```python
class AIReplacementRiskEngine:
    def calculate_automation_risk(self, role: str, skills: List[str]) -> RiskScore
    def identify_future_proof_skills(self, domain: str) -> List[str]
```

**`DomainStabilityEngine`**
```python
class DomainStabilityEngine:
    def calculate_market_volatility(self, domain: str) -> VolatilityScore
    def predict_domain_growth(self, domain: str) -> GrowthPrediction
```

#### Market Analysis (`src/analytics/market_analysis/`)

**`DemandScoreCalculator`**
```python
class DemandScoreCalculator:
    def calculate_skill_demand(self, skill: str, timeframe: str) -> DemandScore
    def calculate_role_demand(self, role: str, location: str) -> DemandScore
```

**`SalaryGrowthEngine`**
```python
class SalaryGrowthEngine:
    def predict_salary_trajectory(self, role: str, experience: int) -> SalaryTrajectory
    def calculate_premium_skills(self, role: str) -> List[SkillPremium]
```

### 4. Machine Learning Components

#### Models (`src/models/`)

**`SalaryPredictor`**
```python
class SalaryPredictor:
    def __init__(self, model_type: str = "random_forest")
    def train(self, X: pd.DataFrame, y: pd.Series) -> None
    def predict(self, features: pd.DataFrame) -> np.ndarray
    def get_feature_importance(self) -> Dict[str, float]
```

**`JobTypeClassifier`**
```python
class JobTypeClassifier:
    def classify_job_type(self, job_description: str, 
                        requirements: List[str]) -> JobType
    def get_classification_confidence(self) -> float
```

---

## 📊 Data Flow Architecture

### Data Pipeline Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   Web       │    │   Raw Data   │    │   Cleaned   │    │   Processed │
│  Scrapers   │───▶│   Storage    │───▶│    Data     │───▶│    Data     │
│             │    │  (CSV/DB)    │    │             │    │  (Features) │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   Rate      │    │   Data       │    │   Feature   │    │   Model     │
│  Limiting   │    │  Validation  │    │ Engineering │    │  Training   │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
                                                                │
                                                                ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌─────────────┐
│   Real-time │    │   Analytics  │    │   ML        │    │   Insights  │
│  Updates    │◀───│   Engines    │◀───│ Predictions │◀───│ Generation  │
└─────────────┘    └──────────────┘    └─────────────┘    └─────────────┘
```

### Data Flow Stages

#### 1. **Ingestion Stage**
- **Web Scraping**: Automated collection from job portals
- **Rate Limiting**: Respectful scraping with configurable delays
- **Error Handling**: Retry logic and failure recovery
- **Data Validation**: Schema validation and quality checks

#### 2. **Processing Stage**
- **Data Cleaning**: Remove duplicates, normalize formats
- **Feature Extraction**: Skill extraction, experience encoding
- **Quality Assurance**: Data completeness and accuracy checks
- **Storage**: Persist cleaned data to MySQL/CSV

#### 3. **Analysis Stage**
- **Analytics Computation**: Calculate demand scores, salary benchmarks
- **ML Predictions**: Generate salary and job type predictions
- **Trend Analysis**: Identify market patterns and insights
- **LLM Processing**: Generate human-readable explanations

#### 4. **Presentation Stage**
- **Dashboard Updates**: Real-time data refresh
- **User Interactions**: Handle filtering and exploration
- **Visualization**: Render charts and insights
- **Export Capabilities**: Download reports and data

---

## 🤖 Machine Learning Pipeline

### Model Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Feature Engineering                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Text      │  │  Numerical  │  │   Categorical       │ │
│  │  Features   │  │  Features  │  │    Features         │ │
│  │  (TF-IDF)   │  │  (Salary)  │  │  (Experience)       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Model Training                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Salary    │  │   Job Type  │  │   Demand           │ │
│  │ Predictor   │  │ Classifier  │  │   Scorer           │ │
│  │ (Regression)│  │ (Classification)│  │ (Regression)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Model Evaluation                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Cross     │  │   Feature   │  │   Performance       │ │
│  │ Validation  │  │ Importance │  │   Metrics           │ │
│  │             │  │ Analysis    │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Model Types & Algorithms

#### 1. **Salary Prediction Model**
- **Algorithm**: Random Forest Regressor
- **Features**: Skills (TF-IDF), Experience Level, Location, Company Size
- **Target**: Annual Salary (INR)
- **Evaluation**: RMSE, MAE, R² Score

#### 2. **Job Type Classification**
- **Algorithm**: Gradient Boosting Classifier
- **Features**: Job Description (TF-IDF), Requirements, Skills
- **Target**: Job Type (Full-time, Internship, Contract, Freelance)
- **Evaluation**: Accuracy, F1-Score, Confusion Matrix

#### 3. **Demand Scoring Model**
- **Algorithm**: Linear Regression with regularization
- **Features**: Posting frequency, salary range, skill requirements
- **Target**: Demand Score (0-100)
- **Evaluation**: Correlation with market indicators

### Feature Engineering Pipeline

```python
class FeaturePipeline:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000)
        self.experience_encoder = OrdinalEncoder()
        self.location_encoder = OneHotEncoder()
        
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        # Text features
        text_features = self.extract_text_features(df['description'])
        
        # Numerical features
        numerical_features = self.extract_numerical_features(df)
        
        # Categorical features
        categorical_features = self.encode_categorical_features(df)
        
        # Combine all features
        return self.combine_features(text_features, numerical_features, categorical_features)
```

---

## 🎯 Analytics Engine Architecture

### Analytics Modules Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 Analytics Engine                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Career    │  │   Domain    │  │   Market            │ │
│  │  Insights   │  │  Analysis   │  │   Analysis          │ │
│  │             │  │             │  │                     │ │
│  │ • Path      │  │ • AI Risk   │  │ • Demand            │ │
│  │ • Role Fit  │  │ • Stability │  │ • Salary            │ │
│  │ • Learning  │  │ • Growth    │  │ • Competition       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                 Entry Barriers                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Hidden    │  │ Interview   │  │   Project            │ │
│  │  Blockers   │  │ Difficulty  │  │   Complexity        │ │
│  │             │  │             │  │                     │ │
│  │ • Education │  │ • Questions │  │ • Requirements      │ │
│  │ • Experience│  │ • Process   │  │ • Timeline          │ │
│  │ • Skills     │  │ • Duration  │  │ • Difficulty        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Career Insights Engine

#### Learning Path Calculation

```python
def calculate_learning_path(current_skills: List[str], 
                          target_role: str) -> LearningPath:
    """
    Calculates optimal learning path from current skills to target role.
    
    Algorithm:
    1. Identify skill gaps between current and required skills
    2. Calculate prerequisite relationships between skills
    3. Estimate learning time based on difficulty and prior knowledge
    4. Optimize path for minimum time and maximum relevance
    """
    
    # Skill gap analysis
    required_skills = get_required_skills(target_role)
    skill_gaps = identify_skill_gaps(current_skills, required_skills)
    
    # Prerequisite mapping
    skill_graph = build_skill_dependency_graph(skill_gaps)
    
    # Time estimation
    learning_times = estimate_learning_times(skill_gaps, user_profile)
    
    # Path optimization
    optimal_path = optimize_learning_sequence(skill_graph, learning_times)
    
    return LearningPath(
        skills=optimal_path,
        total_time=sum(learning_times.values()),
        milestones=generate_milestones(optimal_path)
    )
```

#### Role Fit Evaluation

```python
def evaluate_role_fit(user_profile: UserProfile, role: str) -> FitScore:
    """
    Evaluates how well a user's profile matches a specific role.
    
    Scoring Factors:
    - Skill Match (40%): Direct skill overlap
    - Experience Match (25%): Experience level alignment
    - Education Match (15%): Educational requirements
    - Growth Potential (20%): Future career alignment
    """
    
    skill_score = calculate_skill_match(user_profile.skills, role_requirements)
    experience_score = calculate_experience_match(user_profile.experience, role_level)
    education_score = calculate_education_match(user_profile.education, role_education)
    growth_score = calculate_growth_potential(user_profile, role_career_path)
    
    total_score = (
        skill_score * 0.4 +
        experience_score * 0.25 +
        education_score * 0.15 +
        growth_score * 0.2
    )
    
    return FitScore(
        total=total_score,
        breakdown={
            'skills': skill_score,
            'experience': experience_score,
            'education': education_score,
            'growth': growth_score
        }
    )
```

### Domain Analysis Engine

#### AI Replacement Risk Calculation

```python
def calculate_automation_risk(role: str, skills: List[str]) -> RiskScore:
    """
    Calculates the risk of automation for a given role and skill set.
    
    Risk Factors:
    - Repetitive Task Ratio (30%)
    - Creative/Complex Problem Solving (25%)
    - Human Interaction Requirements (20%)
    - Physical vs Digital Work (15%)
    - Technical Complexity (10%)
    """
    
    role_analysis = analyze_role_characteristics(role)
    skill_analysis = analyze_skill_automation_resistance(skills)
    
    repetitive_score = role_analysis.repetitive_task_ratio
    creative_score = 1 - role_analysis.creative_requirement
    interaction_score = 1 - role_analysis.human_interaction_requirement
    physical_score = role_analysis.physical_work_ratio
    complexity_score = skill_analysis.technical_complexity
    
    risk_score = (
        repetitive_score * 0.3 +
        creative_score * 0.25 +
        interaction_score * 0.2 +
        physical_score * 0.15 +
        (1 - complexity_score) * 0.1
    )
    
    return RiskScore(
        score=risk_score,
        level=categorize_risk_level(risk_score),
        recommendations=generate_mitigation_strategies(risk_score, skills)
    )
```

---

## 🖥️ Dashboard Architecture

### Streamlit Application Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Application                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   App       │  │ Navigation  │  │   Session           │ │
│  │  Entry      │  │   Bar       │  │   Management        │ │
│  │             │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Page Components                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    Home     │  │  Dashboard  │  │   Profile           │ │
│  │   Page      │  │   Pages     │  │   Management        │ │
│  │             │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Shared Components                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Career    │  │   Domain    │  │   Navigation        │ │
│  │  Profiler   │  │  Resolver   │  │    Components       │ │
│  │             │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Page Architecture

#### 1. **Home Page** (`dashboards/pages/home.py`)
- **Purpose**: Landing page with system overview
- **Components**: Hero section, feature highlights, navigation
- **Data**: Global metrics, system statistics

#### 2. **Dashboard Pages**
- **Student Dashboard**: Personalized insights and recommendations
- **Counselor Dashboard**: Aggregate analytics and guidance tools
- **Professional Dashboard**: Advanced market analysis

#### 3. **Profile Management** (`dashboards/pages/set_profile.py`)
- **User Profile Setup**: Skills, experience, preferences
- **Career Goals**: Target roles and aspirations
- **Progress Tracking**: Learning journey monitoring

### Component Architecture

#### Career Profiler (`dashboards/components/career_profiler.py`)

```python
class CareerProfiler:
    def render_profiling_flow(self, navigate_to):
        """
        Multi-step career profiling interface:
        1. Skill Assessment
        2. Experience Evaluation
        3. Career Goal Setting
        4. Learning Path Generation
        """
        
        # Step management
        if 'profile_step' not in st.session_state:
            st.session_state.profile_step = 1
            
        # Render current step
        if st.session_state.profile_step == 1:
            self.render_skill_assessment()
        elif st.session_state.profile_step == 2:
            self.render_experience_evaluation()
        elif st.session_state.profile_step == 3:
            self.render_career_goals()
        elif st.session_state.profile_step == 4:
            self.render_learning_path()
```

#### Domain Confusion Resolver (`dashboards/components/domain_confusion_resolver.py`)

```python
class DomainConfusionResolver:
    def resolve_domain_confusion(self, user_skills: List[str]) -> DomainRecommendation:
        """
        Helps users choose between similar domains based on their skills.
        
        Process:
        1. Identify similar domains
        2. Compare skill requirements
        3. Analyze market opportunities
        4. Provide recommendations
        """
        
        similar_domains = self.find_similar_domains(user_skills)
        domain_comparison = self.compare_domains(similar_domains, user_skills)
        market_analysis = self.analyze_market_opportunities(similar_domains)
        
        return self.generate_recommendations(domain_comparison, market_analysis)
```

### State Management

#### Session State Structure

```python
# User Profile Data
st.session_state.user_profile = {
    'skills': [],
    'experience': 0,
    'education': '',
    'career_goals': [],
    'preferences': {}
}

# Application State
st.session_state.current_page = 'Home'
st.session_state.profile_step = 1
st.session_state.show_prediction = False

# Data State
st.session_state.df = None  # Main dataset
st.session_state.global_analytics = {}
st.session_state.user_analytics = {}
```

#### Data Loading Strategy

```python
def load_dataframe():
    """
    Lazy loading strategy for large datasets:
    1. Check if data exists in session state
    2. Load from cache if available
    3. Load from storage and cache if not available
    """
    
    if 'df' in st.session_state and st.session_state.df is not None:
        return st.session_state.df
    
    # Load from storage
    df = load_from_database()
    
    # Cache in session state
    st.session_state.df = df
    
    return df
```

---

## 🗄️ Data Storage Architecture

### Database Schema

#### MySQL Tables Structure

```sql
-- Job Postings Table
CREATE TABLE job_postings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    location VARCHAR(100),
    salary_min DECIMAL(10,2),
    salary_max DECIMAL(10,2),
    experience_required VARCHAR(50),
    skills TEXT,
    description TEXT,
    job_type ENUM('full-time', 'part-time', 'contract', 'internship'),
    posted_date DATE,
    scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50),
    INDEX idx_location (location),
    INDEX idx_salary (salary_min, salary_max),
    INDEX idx_skills (skills(100)),
    INDEX idx_posted_date (posted_date)
);

-- Skills Master Table
CREATE TABLE skills_master (
    id INT PRIMARY KEY AUTO_INCREMENT,
    skill_name VARCHAR(100) UNIQUE,
    category VARCHAR(50),
    demand_score DECIMAL(5,2),
    average_salary_premium DECIMAL(5,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Profiles Table
CREATE TABLE user_profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(50) UNIQUE,
    skills JSON,
    experience_level INT,
    education_level VARCHAR(50),
    career_goals JSON,
    preferences JSON,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics Cache Table
CREATE TABLE analytics_cache (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cache_key VARCHAR(255) UNIQUE,
    cache_data JSON,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Data Storage Strategy

```python
class StorageStrategy:
    """
    Multi-tier storage strategy:
    1. Hot Data (Redis/Session): Frequently accessed data
    2. Warm Data (MySQL): Structured data with complex queries
    3. Cold Data (CSV/Files): Historical data and backups
    """
    
    def store_job_postings(self, jobs: List[JobPosting]) -> None:
        """
        Store job postings with appropriate strategy:
        - Recent jobs (< 30 days): MySQL with indexes
        - Historical jobs: CSV files for archiving
        """
        
        recent_jobs = [job for job in jobs if self.is_recent(job.posted_date)]
        historical_jobs = [job for job in jobs if not self.is_recent(job.posted_date)]
        
        # Store recent jobs in MySQL
        self.mysql_store.store_batch(recent_jobs)
        
        # Archive historical jobs
        self.csv_store.archive_batch(historical_jobs)
```

### Data Access Layer

#### Repository Pattern Implementation

```python
class JobPostingRepository:
    """
    Repository pattern for data access abstraction
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def find_by_location(self, location: str, limit: int = 100) -> List[JobPosting]:
        query = """
        SELECT * FROM job_postings 
        WHERE location LIKE %s 
        ORDER BY posted_date DESC 
        LIMIT %s
        """
        return self.db.execute_query(query, (f"%{location}%", limit))
    
    def find_by_skills(self, skills: List[str]) -> List[JobPosting]:
        skill_conditions = " OR ".join(["skills LIKE %s"] * len(skills))
        query = f"""
        SELECT * FROM job_postings 
        WHERE ({skill_conditions})
        ORDER BY posted_date DESC
        """
        params = tuple([f"%{skill}%" for skill in skills])
        return self.db.execute_query(query, params)
    
    def get_salary_statistics(self, role: str, location: str = None) -> SalaryStats:
        base_query = "SELECT AVG(salary_min), AVG(salary_max), COUNT(*) FROM job_postings WHERE title LIKE %s"
        params = (f"%{role}%",)
        
        if location:
            base_query += " AND location LIKE %s"
            params = (f"%{role}%", f"%{location}%")
        
        result = self.db.execute_query(base_query, params)
        return SalaryStats.from_db_result(result)
```

---

## 🔐 Security & Performance

### Security Architecture

#### 1. **Data Protection**
- **Environment Variables**: Sensitive data stored in `.env` files
- **Database Security**: Encrypted connections, least privilege access
- **Input Validation**: Comprehensive validation for all user inputs
- **SQL Injection Prevention**: Parameterized queries, ORM usage

#### 2. **Scraping Ethics**
- **Rate Limiting**: Respectful scraping with configurable delays
- **User-Agent Rotation**: Prevent IP blocking
- **Terms of Service Compliance**: Adhere to website scraping policies
- **Data Privacy**: Anonymize personal information

#### 3. **Access Control**
```python
class AccessControl:
    """
    Role-based access control for different user types
    """
    
    PERMISSIONS = {
        'student': ['view_dashboard', 'update_profile', 'export_personal_data'],
        'counselor': ['view_dashboard', 'update_profile', 'export_analytics', 'view_aggregate_data'],
        'admin': ['all_permissions']
    }
    
    def check_permission(self, user_role: str, action: str) -> bool:
        return action in self.PERMISSIONS.get(user_role, [])
```

### Performance Optimization

#### 1. **Caching Strategy**
```python
class CacheManager:
    """
    Multi-level caching:
    1. Memory Cache (Session): User-specific data
    2. Redis Cache: Shared data across sessions
    3. Database Cache: Query result caching
    """
    
    def get_analytics(self, cache_key: str, compute_func) -> Any:
        # Check memory cache
        if cache_key in st.session_state:
            return st.session_state[cache_key]
        
        # Check Redis cache
        cached_result = self.redis_client.get(cache_key)
        if cached_result:
            st.session_state[cache_key] = cached_result
            return cached_result
        
        # Compute and cache
        result = compute_func()
        self.redis_client.setex(cache_key, 3600, result)
        st.session_state[cache_key] = result
        
        return result
```

#### 2. **Database Optimization**
- **Indexing Strategy**: Optimized indexes for common queries
- **Query Optimization**: Efficient SQL with proper joins
- **Connection Pooling**: Reuse database connections
- **Batch Processing**: Bulk operations for large datasets

#### 3. **Frontend Performance**
- **Lazy Loading**: Load data on demand
- **Component Memoization**: Cache expensive computations
- **Efficient State Management**: Minimize session state size
- **Optimized Rendering**: Prevent unnecessary re-renders

---

## 🚀 Deployment Architecture

### Development Environment

```
┌─────────────────────────────────────────────────────────────┐
│                    Development Setup                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Local     │  │   MySQL     │  │   Streamlit         │ │
│  │  Python     │  │  Database   │  │   Development       │ │
│  │ Environment │  │             │  │   Server            │ │
│  │             │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Production Deployment (Planned)

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Architecture                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Load      │  │   Streamlit │  │   MySQL Cluster     │ │
│  │  Balancer   │  │   Cluster   │  │   (Primary/Replica) │ │
│  │             │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Supporting Services                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Redis     │  │   Monitor   │  │   Logging            │ │
│  │   Cache     │  │   (Grafana) │  │   (ELK Stack)        │ │
│  │             │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Containerization Strategy

#### Docker Configuration

```dockerfile
# Dockerfile for Streamlit Application
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DB_HOST=mysql
      - REDIS_HOST=redis
    depends_on:
      - mysql
      - redis
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: job_trends
    volumes:
      - mysql_data:/var/lib/mysql
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

### Monitoring & Observability

#### 1. **Application Monitoring**
- **Health Checks**: Application and database connectivity
- **Performance Metrics**: Response times, error rates
- **Resource Usage**: CPU, memory, disk utilization
- **Business Metrics**: User engagement, feature usage

#### 2. **Logging Strategy**
```python
# Structured logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
```

#### 3. **Error Handling**
```python
class ErrorHandler:
    """
    Centralized error handling and reporting
    """
    
    def handle_scraping_error(self, error: Exception, context: dict) -> None:
        """
        Handle scraping-specific errors with appropriate recovery strategies
        """
        
        if isinstance(error, TimeoutException):
            self.logger.warning(f"Timeout occurred: {context}")
            self.apply_backoff_strategy(context)
        
        elif isinstance(error, BlockedException):
            self.logger.error(f"IP blocked: {context}")
            self.notify_admin(context)
            self.switch_proxy()
        
        else:
            self.logger.error(f"Unexpected error: {error}", exc_info=True)
            self.capture_exception(error, context)
```

---

## 🔄 Continuous Integration & Deployment

### CI/CD Pipeline

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Code Commit   │───▶│   Build & Test  │───▶│   Security Scan │
│                 │    │                 │    │                 │
│ • Git Push      │    │ • Unit Tests    │    │ • Vulnerability │
│ • PR Created    │    │ • Integration   │    │ • Dependency    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Deploy to     │◀───│   Quality Gate  │───▶│   Deploy to     │
│   Staging       │    │                 │    │   Production    │
│                 │    │ • Coverage >80% │    │                 │
│ • Smoke Tests   │    │ • Performance  │    │ • Blue/Green    │
│ • E2E Tests     │    │ • Manual Review│    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### GitHub Actions Workflow

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security scan
      run: |
        pip install safety bandit
        safety check
        bandit -r src/

  deploy:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        # Deployment commands
        echo "Deploying to production..."
```

---

This technical architecture documentation provides a comprehensive overview of the Job Market Intelligence System's design, components, data flow, and deployment strategies. It serves as a reference for developers, system architects, and DevOps engineers working on the project.

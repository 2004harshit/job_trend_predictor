# Job Scraping Pipeline - Usage Guide

## Overview

This pipeline system supports two types of job data extraction:

1. **General Pipeline**: Scrapes general job postings and stores data in CSV format
2. **Fresher Pipeline**: Scrapes fresher/entry-level job postings and stores data in MySQL database

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    run_pipeline.py                          │
│                (Pipeline Orchestrator)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─────────────────┬──────────────────┐
                            ▼                 ▼                  ▼
                    ┌───────────────┐  ┌──────────────┐  ┌──────────────┐
                    │    General    │  │   Fresher    │  │     All      │
                    │   Pipeline    │  │   Pipeline   │  │  Pipelines   │
                    └───────────────┘  └──────────────┘  └──────────────┘
                            │                 │
                            ▼                 ▼
                ┌──────────────────┐  ┌─────────────────┐
                │ NaukriExtractor  │  │FresherExtractor │
                └──────────────────┘  └─────────────────┘
                            │                 │
                            ▼                 ▼
                ┌──────────────────┐  ┌─────────────────┐
                │  CSV Storage     │  │ MySQL Storage   │
                └──────────────────┘  └─────────────────┘
```

## Prerequisites

### 1. Python Environment
```bash
# Python 3.8 or higher required
python --version

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup (for Fresher Pipeline)
```sql
-- Create database
CREATE DATABASE job_trends;

-- Create fresher_jobs table
CREATE TABLE fresher_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    location VARCHAR(255),
    experience VARCHAR(100),
    salary VARCHAR(100),
    job_description TEXT,
    skills TEXT,
    job_url VARCHAR(500) UNIQUE,
    posted_date DATE,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_job_title (job_title),
    INDEX idx_company (company),
    INDEX idx_location (location),
    INDEX idx_posted_date (posted_date)
);
```

### 3. Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your credentials
# DB_USER=your_username
# DB_PASSWORD=your_password
```

## Configuration

Edit `config.yaml` to customize:

### Pipeline Settings
```yaml
pipeline:
  max_pages: 10           # Maximum pages to scrape per job role
  per_page_limit: 15      # Jobs per page
  min_delay: 3            # Minimum delay between requests (seconds)
  max_delay: 7            # Maximum delay between requests (seconds)
  role_delay: 20          # Delay between different job roles (seconds)
```

### Job Groups
```yaml
job_queue:
  group1:
    - "Data Scientist"
    - "Machine Learning Engineer"
    - "Data Analyst"
  group2:
    - "Business Analyst"
    - "AI Engineer"
    - "Research Associate"
```

## Usage

### Basic Commands

#### 1. Run General Pipeline (CSV Storage)
```bash
# Run all general jobs
python run_pipeline.py --mode general

# Run specific group
python run_pipeline.py --mode general --group group1

# Run with custom config
python run_pipeline.py --mode general --config custom_config.yml
```

#### 2. Run Fresher Pipeline (MySQL Storage)
```bash
# Run all fresher jobs
python run_pipeline.py --mode fresher

# Run specific group
python run_pipeline.py --mode fresher --group group1
```

#### 3. Run Both Pipelines
```bash
# Run both pipelines for all jobs
python run_pipeline.py --mode all

# Run both pipelines for specific group
python run_pipeline.py --mode all --group group2
```

### Advanced Usage

#### Run Specific Groups
```bash
# Run only group1 jobs
python run_pipeline.py --mode general --group group1

# Run only group3 fresher jobs
python run_pipeline.py --mode fresher --group group3
```

#### Custom Configuration
```bash
# Use a different config file
python run_pipeline.py --mode general --config production_config.yml
```

## Output

### General Pipeline Output
- **Location**: `etl_pipeline/data/raw/general_jobs.csv`
- **Format**: CSV with columns:
  - job_title
  - company
  - location
  - experience
  - salary
  - job_description
  - skills
  - job_url
  - posted_date
  - scraped_at

### Fresher Pipeline Output
- **Location**: MySQL database `job_trends.fresher_jobs` table
- **Access**: Use any MySQL client or Python script to query

## Monitoring & Logs

### Log Files
```
logs/
├── pipeline.log          # General pipeline logs
└── pipeline_error.log    # Error logs only
```

### View Logs
```bash
# View latest logs
tail -f logs/pipeline.log

# View errors only
tail -f logs/pipeline_error.log

# Search for specific job
grep "Data Scientist" logs/pipeline.log
```

## Scheduling with Cron/Task Scheduler

### Linux/Mac (Cron)
```bash
# Edit crontab
crontab -e

# Add daily job at 2 AM
0 2 * * * cd /path/to/project && /path/to/venv/bin/python run_pipeline.py --mode all >> logs/cron.log 2>&1
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily at 2 AM)
4. Set action: 
   - Program: `python`
   - Arguments: `run_pipeline.py --mode all`
   - Start in: `/path/to/project`

## Airflow Integration

### DAG Example
```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 2, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'job_scraping_pipeline',
    default_args=default_args,
    description='Daily job scraping pipeline',
    schedule_interval='0 2 * * *',  # 2 AM daily
    catchup=False
)

# Task 1: General jobs
general_task = BashOperator(
    task_id='scrape_general_jobs',
    bash_command='cd /path/to/project && python run_pipeline.py --mode general',
    dag=dag
)

# Task 2: Fresher jobs
fresher_task = BashOperator(
    task_id='scrape_fresher_jobs',
    bash_command='cd /path/to/project && python run_pipeline.py --mode fresher',
    dag=dag
)

# Set dependencies
general_task >> fresher_task
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```
Error: Can't connect to MySQL server
```
**Solution**: 
- Check `.env` file has correct credentials
- Verify MySQL service is running
- Check firewall settings

#### 2. Import Error
```
ModuleNotFoundError: No module named 'NaukriExtractor'
```
**Solution**:
- Verify project structure
- Check PYTHONPATH
- Ensure all dependencies are installed

#### 3. Rate Limiting
```
Error: Too many requests (429)
```
**Solution**:
- Increase `min_delay` and `max_delay` in config.yaml
- Reduce `max_pages` or `per_page_limit`
- Add random user agent rotation

#### 4. Configuration Not Found
```
FileNotFoundError: Configuration file not found
```
**Solution**:
- Ensure config.yaml is in the correct location
- Use `--config` flag to specify path
- Check file permissions

### Debug Mode

```bash
# Run with verbose logging
LOG_LEVEL=DEBUG python run_pipeline.py --mode general

# Check specific component
python -c "from run_pipeline import PipelineOrchestrator; 
           o = PipelineOrchestrator(); 
           print(o.config)"
```

## Performance Optimization

### 1. Parallel Processing
Modify config to run groups in parallel:
```yaml
pipeline:
  parallel_groups: true
  max_workers: 3
```

### 2. Database Batch Inserts
```yaml
database:
  batch_size: 100  # Insert 100 records at once
```

### 3. Reduce Delays (Use Responsibly)
```yaml
pipeline:
  min_delay: 1
  max_delay: 3
  # Note: Too aggressive scraping may get IP blocked
```

## Data Analysis Examples

### Query Fresher Jobs
```python
import mysql.connector

conn = mysql.connector.connect(
    host='localhost',
    user='your_user',
    password='your_password',
    database='job_trends'
)

cursor = conn.cursor()
cursor.execute("""
    SELECT job_title, company, location, COUNT(*) as count
    FROM fresher_jobs
    GROUP BY job_title, company, location
    ORDER BY count DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(row)
```

### Analyze CSV Data
```python
import pandas as pd

df = pd.read_csv('etl_pipeline/data/raw/general_jobs.csv')

# Top hiring companies
print(df['company'].value_counts().head(10))

# Jobs by location
print(df['location'].value_counts().head(10))

# Average experience required
print(df['experience'].value_counts())
```

## Contributing

1. Create feature branch
2. Make changes
3. Write tests
4. Submit pull request

## License

MIT License

## Support

For issues or questions:
- Email: support@example.com
- GitHub Issues: https://github.com/yourrepo/issues
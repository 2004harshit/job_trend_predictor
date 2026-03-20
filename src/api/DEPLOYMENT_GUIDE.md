# Deployment Guide for Job Trend Predictor API

## 🚀 Production Deployment on Render

This guide covers deploying the Job Trend Predictor API with PostgreSQL database on Render.com.

## 📋 Prerequisites

### 1. PostgreSQL Database on Render
- Create a PostgreSQL database on Render
- Note the connection details (host, port, database name, user, password)

### 2. Environment Variables
Set up the following environment variables in your Render service:

```bash
# Database Configuration
DB_HOST=your-db-host.render.com
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_SSLMODE=require

# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

## 🗄️ Database Setup

### 1. Create Database Schema

Connect to your PostgreSQL database and run the schema:

```bash
# Connect to your database
psql -h your-db-host.render.com -p 5432 -U your_username -d your_database_name

# Run the schema
\i database_schema.sql
```

### 2. Migrate Data (Optional)

If you have existing CSV data, migrate it to PostgreSQL:

```python
# migration_script.py
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os

def migrate_csv_to_postgres(csv_path, db_config):
    """Migrate CSV data to PostgreSQL"""
    
    # Read CSV data
    df = pd.read_csv(csv_path)
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    # Insert data
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO job_listings (
                job_type, skills, min_experience, max_experience,
                location, salary_lakhs, company, posted_date,
                no_of_applicants, no_of_openings
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row.get('Job_Type'),
            row.get('Skills'),
            row.get('Min_Experience'),
            row.get('Max_Experience'),
            row.get('Location'),
            row.get('Salary_Lakhs'),
            row.get('Company'),
            row.get('Posted_Date'),
            row.get('No of applicant applied cleaned'),
            row.get('No of job opening cleaned ')
        ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Migrated {len(df)} records to PostgreSQL")

if __name__ == "__main__":
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    migrate_csv_to_postgres('data/processed/cleaned/cleaned_job_data.csv', db_config)
```

## 🔧 Configuration Files

### 1. requirements.txt (Updated)

Make sure your requirements.txt includes:
```
Flask==2.3.3
Flask-CORS==4.0.0
psycopg2-binary==2.9.7
pandas==2.0.3
gunicorn==21.2.0
python-dotenv==1.0.0
```

### 2. Procfile

Create a `Procfile` in your project root:

```procfile
web: gunicorn --bind 0.0.0.0:$PORT src.api.routes:app
```

### 3. runtime.txt

Create a `runtime.txt` file:

```
python-3.9.16
```

## 🚀 Deployment Steps

### 1. Push to GitHub

```bash
git add .
git commit -m "Add PostgreSQL support for production deployment"
git push origin main
```

### 2. Create Web Service on Render

1. Go to Render Dashboard
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure build settings:
   - Build Command: `pip install -r src/api/requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT src.api.routes:app`

### 3. Create PostgreSQL Database

1. Click "New +" → "PostgreSQL"
2. Configure database settings
3. Note the connection details

### 4. Set Environment Variables

In your web service settings, add the environment variables:

```bash
DB_HOST=your-db-host.render.com
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
DB_SSLMODE=require
```

### 5. Deploy

Click "Deploy" and wait for the build to complete.

## 🧪 Testing the Deployment

### 1. Health Check

```bash
curl https://your-app-name.onrender.com/api/health
```

### 2. Test Recommendations

```bash
curl -X POST https://your-app-name.onrender.com/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "skills": ["Python", "SQL", "Machine Learning"],
    "experience": "Fresher",
    "location": "Bangalore",
    "top_n": 3
  }'
```

### 3. Test Data Stats

```bash
curl https://your-app-name.onrender.com/api/data/stats
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Errors

**Error**: `could not connect to server`

**Solution**:
- Check environment variables
- Verify database is running
- Ensure SSL mode is correct

#### 2. Module Import Errors

**Error**: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution**:
- Ensure `psycopg2-binary` is in requirements.txt
- Check build logs for installation errors

#### 3. Application Startup Errors

**Error**: `Application failed to start`

**Solution**:
- Check logs in Render dashboard
- Verify Procfile syntax
- Ensure correct Python version

### Debugging Steps

1. **Check Logs**: Go to Render Dashboard → Your Service → Logs
2. **Test Database**: Connect to database and run test queries
3. **Environment Variables**: Verify all required variables are set
4. **Local Testing**: Test locally with same environment variables

## 📊 Monitoring

### 1. Health Monitoring

The API includes a health check endpoint:
```bash
GET /api/health
```

### 2. Database Monitoring

Monitor database performance and connections:
- Connection pool usage
- Query performance
- Database size

### 3. Application Metrics

Monitor:
- Response times
- Error rates
- Request volume

## 🔒 Security

### 1. Database Security

- Use SSL connections
- Limit database user permissions
- Use environment variables for credentials

### 2. API Security

- Enable CORS only for trusted domains
- Validate all inputs
- Use HTTPS (automatic on Render)

## 📈 Performance Optimization

### 1. Database Optimization

- Add indexes for frequently queried columns
- Use connection pooling
- Optimize queries

### 2. Application Optimization

- Enable caching (Redis)
- Use Gunicorn workers
- Optimize imports

### 3. Render Optimization

- Use appropriate instance type
- Enable auto-scaling
- Configure health checks

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Render
      run: |
        curl -X POST \
          -H "Authorization: Bearer ${{ secrets.RENDER_API_KEY }}" \
          -H "Content-Type: application/json" \
          -d '{"serviceId": "your-service-id"}' \
          https://api.render.com/v1/services/your-service-id/deploys
```

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/current/best-practices.html)

## 🆘 Support

If you encounter issues:

1. Check Render documentation
2. Review application logs
3. Test database connectivity
4. Verify environment variables
5. Create a support ticket with Render

---

**Last Updated**: 2025-03-18
**Version**: 1.0.0

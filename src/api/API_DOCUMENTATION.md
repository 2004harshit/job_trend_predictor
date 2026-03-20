# Job Trend Predictor API Documentation

## Overview

The Job Trend Predictor API provides endpoints for domain recommendations based on user profiles using the RuleBasedRecommender engine.

## Base URL

```
http://localhost:5000
```

## Authentication

Currently, no authentication is required (for development purposes).

## Endpoints

### 1. Health Check

**GET** `/api/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-03-18T09:40:00.000Z",
  "service": "Job Trend Predictor API",
  "version": "1.0.0"
}
```

### 2. Get Recommendations

**POST** `/api/recommend`

Get domain recommendations based on user profile.

**Request Body:**
```json
{
  "skills": ["Python", "SQL", "Machine Learning"],
  "experience": "Fresher",
  "location": "Bangalore",
  "math_comfort": "Moderate",
  "top_n": 3
}
```

**Parameters:**
- `skills` (required): List of user skills
- `experience` (required): One of ["Fresher", "1-2 years", "3-5 years", "5+ years"]
- `location` (required): User location
- `math_comfort` (optional): One of ["Weak", "Moderate", "Strong"]
- `top_n` (optional): Number of recommendations (1-10, default: 3)

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-03-18T09:40:00.000Z",
  "user_profile": {
    "skills": ["Python", "SQL", "Machine Learning"],
    "experience": "Fresher",
    "location": "Bangalore",
    "math_comfort": "Moderate",
    "top_n": 3
  },
  "recommendations": [
    {
      "domain": "data scientist",
      "match_percentage": 75,
      "reasoning": "Good skill match with moderate competition",
      "pros": ["High demand", "Good salary prospects"],
      "cons": ["Competitive market", "Requires strong math skills"]
    }
  ],
  "total_recommendations": 3
}
```

### 3. Get All Domains

**GET** `/api/recommend/domains`

Get all available domains for recommendations.

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-03-18T09:40:00.000Z",
  "domains": ["data scientist", "software engineer", "ml engineer", "data analyst"],
  "total_domains": 4
}
```

### 4. Analyze Domain

**POST** `/api/recommend/analyze`

Get detailed analysis for a specific domain.

**Request Body:**
```json
{
  "domain": "data scientist",
  "user_profile": {
    "skills": ["Python", "SQL"],
    "experience": "Fresher",
    "location": "Bangalore"
  }
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "domain": "data scientist",
    "user_profile": {
      "skills": ["Python", "SQL"],
      "experience": "Fresher",
      "location": "Bangalore"
    },
    "market_signals": {
      "demand_score": 8.5,
      "comp_level": "Medium",
      "sat_risk": "Safe",
      "growth_trend": 7.8
    },
    "score_breakdown": {
      "skill_score": 25.0,
      "market_score": 25.5,
      "feasibility_score": 20.0,
      "math_penalty": 0.0,
      "total_score": 70.5
    },
    "detailed_analysis": {
      "domain": "data scientist",
      "match_percentage": 70.5,
      "reasoning": "Good skill match with moderate competition",
      "pros": ["High demand", "Good salary prospects"],
      "cons": ["Competitive market"]
    },
    "timestamp": "2025-03-18T09:40:00.000Z"
  }
}
```

### 5. Compare Domains

**POST** `/api/recommend/compare`

Compare multiple domains for a user profile.

**Request Body:**
```json
{
  "domains": ["data scientist", "software engineer", "ml engineer"],
  "user_profile": {
    "skills": ["Python", "SQL"],
    "experience": "Fresher",
    "location": "Bangalore"
  }
}
```

**Response:**
```json
{
  "success": true,
  "timestamp": "2025-03-18T09:40:00.000Z",
  "user_profile": {
    "skills": ["Python", "SQL"],
    "experience": "Fresher",
    "location": "Bangalore"
  },
  "comparisons": [
    {
      "domain": "data scientist",
      "score_breakdown": {
        "skill_score": 25.0,
        "market_score": 25.5,
        "feasibility_score": 20.0,
        "math_penalty": 0.0,
        "total_score": 70.5
      },
      "detailed_analysis": {
        "domain": "data scientist",
        "match_percentage": 70.5,
        "reasoning": "Good skill match with moderate competition"
      },
      "market_signals": {
        "demand_score": 8.5,
        "comp_level": "Medium",
        "sat_risk": "Safe"
      }
    }
  ],
  "ranking_summary": [
    {
      "rank": 1,
      "domain": "data scientist",
      "total_score": 70.5,
      "match_percentage": 70.5
    }
  ]
}
```

### 6. Get Market Signals

**GET** `/api/market/signals/<domain>`

Get market signals for a specific domain.

**Query Parameters:**
- `location` (optional): Location for market analysis (default: Bangalore)

**Response:**
```json
{
  "success": true,
  "domain": "data scientist",
  "location": "Bangalore",
  "market_signals": {
    "demand_score": 8.5,
    "comp_level": "Medium",
    "sat_risk": "Safe",
    "growth_trend": 7.8
  },
  "timestamp": "2025-03-18T09:40:00.000Z"
}
```

### 7. Get Data Statistics

**GET** `/api/data/stats`

Get statistics about the job data.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_records": 100,
    "job_types": {
      "data scientist": 20,
      "software engineer": 20,
      "ml engineer": 20,
      "data analyst": 20,
      "backend developer": 20
    },
    "experience_distribution": {
      "0": 20,
      "1": 20,
      "2": 20,
      "3": 20,
      "4": 20
    },
    "location_distribution": {
      "Bangalore": 20,
      "Hyderabad": 20,
      "Pune": 20,
      "Chennai": 20,
      "Mumbai": 20
    },
    "salary_stats": {
      "mean": 10.2,
      "median": 10.0,
      "min": 6.0,
      "max": 15.0
    },
    "data_columns": ["Job_Type", "Skills", "Min_Experience", "Max_Experience", "Location", "Salary_Lakhs"],
    "last_updated": "2025-03-18T09:40:00.000Z"
  }
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": "Additional error details (if available)"
}
```

### Common Error Codes

- **400 Bad Request**: Invalid input data
- **404 Not Found**: Endpoint or domain not found
- **500 Internal Server Error**: Server-side error

## Usage Examples

### Using curl

```bash
# Get recommendations
curl -X POST http://localhost:5000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "skills": ["Python", "SQL", "Machine Learning"],
    "experience": "Fresher",
    "location": "Bangalore",
    "top_n": 3
  }'

# Get all domains
curl http://localhost:5000/api/recommend/domains

# Health check
curl http://localhost:5000/api/health
```

### Using Python

```python
import requests

# Get recommendations
response = requests.post('http://localhost:5000/api/recommend', json={
    "skills": ["Python", "SQL", "Machine Learning"],
    "experience": "Fresher",
    "location": "Bangalore",
    "top_n": 3
})

if response.status_code == 200:
    data = response.json()
    print("Recommendations:", data['recommendations'])
else:
    print("Error:", response.json())
```

### Using JavaScript

```javascript
// Get recommendations
const response = await fetch('http://localhost:5000/api/recommend', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    skills: ["Python", "SQL", "Machine Learning"],
    experience: "Fresher",
    location: "Bangalore",
    top_n: 3
  })
});

const data = await response.json();
console.log('Recommendations:', data.recommendations);
```

## Running the API

### Development

```bash
# Install dependencies
pip install -r src/api/requirements.txt

# Run the API
python src/api/routes.py
```

### Production (using Gunicorn)

```bash
# Install gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 src.api.routes:app
```

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider implementing rate limiting using Flask-Limiter or similar.

## CORS

CORS is enabled for all origins in development. For production, configure appropriate origins.

## Logging

The API uses Python's logging module. Logs are printed to the console by default.

## Data Source

The API uses job data from `data/processed/cleaned/cleaned_job_data.csv`. If the file is not found, it uses sample data for testing.

## Dependencies

- Flask 2.3.3
- Flask-CORS 4.0.0
- pandas 2.0.3
- numpy 1.24.3

## Testing

Run tests using pytest:

```bash
pytest src/api/tests/
```

## Support

For issues and questions, please refer to the project documentation or create an issue in the repository.

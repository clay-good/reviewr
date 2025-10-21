# 📊 reviewr Dashboard Guide

Comprehensive guide to the reviewr web dashboard for tracking code quality metrics and trends.

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Integration](#integration)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

The reviewr dashboard provides a web-based interface for:

✅ **Tracking code quality** - Monitor issues, trends, and metrics over time  
✅ **Project management** - Manage multiple projects in one place  
✅ **Review history** - View all past code reviews and findings  
✅ **Analytics** - Visualize trends and identify patterns  
✅ **Team insights** - Track team performance and code quality  
✅ **REST API** - Programmatic access to all data  

### Features

- **Real-time dashboard** - Live metrics and statistics
- **Project tracking** - Monitor multiple projects
- **Review history** - Complete audit trail of all reviews
- **Finding management** - Track, filter, and manage code issues
- **Trend analysis** - Visualize quality trends over time
- **REST API** - Full API for integration
- **SQLite/PostgreSQL** - Flexible database options
- **Auto-refresh** - Dashboard updates automatically

---

## Quick Start

### 1. Install Dependencies

```bash
pip install fastapi uvicorn sqlalchemy
```

### 2. Start the Dashboard

```bash
# Start with default settings
reviewr dashboard start

# Or specify custom port
reviewr dashboard start --port 8080

# Development mode with auto-reload
reviewr dashboard start --reload
```

### 3. Open in Browser

```
http://localhost:8000
```

### 4. View API Documentation

```
http://localhost:8000/docs
```

---

## Installation

### Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- SQLAlchemy
- (Optional) PostgreSQL for production

### Install from Source

```bash
cd reviewr
pip install -e .
pip install fastapi uvicorn sqlalchemy
```

### Database Setup

#### SQLite (Default)

```bash
# Initialize database
reviewr dashboard init-db

# Database file: reviewr.db
```

#### PostgreSQL (Production)

```bash
# Install PostgreSQL driver
pip install psycopg2-binary

# Initialize with PostgreSQL
reviewr dashboard init-db --database-url postgresql://user:pass@localhost/reviewr
```

---

## Usage

### Starting the Dashboard

```bash
# Basic start
reviewr dashboard start

# Custom host and port
reviewr dashboard start --host 0.0.0.0 --port 8080

# Development mode
reviewr dashboard start --reload

# Custom database
reviewr dashboard start --database-url postgresql://user:pass@localhost/reviewr
```

### Managing Projects

```bash
# Add a project
reviewr dashboard add-project my-app --language python --repository-url https://github.com/user/repo

# List projects
reviewr dashboard list-projects

# Show statistics
reviewr dashboard stats
```

### Integrating with Reviews

When running code reviews, send results to the dashboard:

```python
from reviewr.dashboard.database import DatabaseManager

# Initialize database
db = DatabaseManager()

# Add review
review = db.add_review(
    project_name="my-app",
    commit_sha="abc123",
    branch="main",
    pr_number=42,
    author="developer",
    provider="claude"
)

# Add findings
for finding in findings:
    db.add_finding(
        review_id=review.id,
        type=finding.type,
        severity=finding.severity,
        file_path=finding.file_path,
        line_start=finding.line_start,
        line_end=finding.line_end,
        message=finding.message,
        confidence=finding.confidence
    )

# Update review status
session = db.get_session()
review.status = 'completed'
review.completed_at = datetime.utcnow()
review.total_findings = len(findings)
session.commit()
```

---

## API Reference

### Base URL

```
http://localhost:8000/api
```

### Authentication

Currently no authentication required. Add authentication for production use.

### Endpoints

#### Projects

**Create Project**
```http
POST /api/projects
Content-Type: application/json

{
  "name": "my-app",
  "repository_url": "https://github.com/user/repo",
  "description": "My application",
  "language": "python"
}
```

**List Projects**
```http
GET /api/projects?skip=0&limit=50
```

**Get Project**
```http
GET /api/projects/{project_id}
```

#### Reviews

**Create Review**
```http
POST /api/reviews
Content-Type: application/json

{
  "project_name": "my-app",
  "commit_sha": "abc123",
  "branch": "main",
  "pr_number": 42,
  "author": "developer",
  "provider": "claude"
}
```

**List Reviews**
```http
GET /api/reviews?project_id=1&skip=0&limit=50
```

**Get Review**
```http
GET /api/reviews/{review_id}
```

**Update Review**
```http
PATCH /api/reviews/{review_id}
Content-Type: application/json

{
  "status": "completed",
  "total_findings": 10,
  "critical_findings": 2
}
```

#### Findings

**Create Finding**
```http
POST /api/findings
Content-Type: application/json

{
  "review_id": 1,
  "type": "security",
  "severity": "high",
  "category": "sql_injection",
  "file_path": "app.py",
  "line_start": 10,
  "line_end": 15,
  "message": "SQL injection vulnerability",
  "confidence": 0.95
}
```

**List Findings**
```http
GET /api/findings?review_id=1&severity=high&skip=0&limit=100
```

#### Analytics

**Overview Metrics**
```http
GET /api/metrics/overview
```

Response:
```json
{
  "total_projects": 5,
  "total_reviews": 100,
  "total_findings": 500,
  "avg_findings_per_review": 5.0,
  "critical_findings": 10,
  "high_findings": 50
}
```

**Project Trends**
```http
GET /api/metrics/trends/{project_id}?days=30
```

Response:
```json
{
  "total_issues": [
    {"date": "2024-01-01", "value": 10},
    {"date": "2024-01-02", "value": 8}
  ],
  "critical_issues": [
    {"date": "2024-01-01", "value": 2},
    {"date": "2024-01-02", "value": 1}
  ],
  "overall_score": [
    {"date": "2024-01-01", "value": 85.0},
    {"date": "2024-01-02", "value": 90.0}
  ]
}
```

---

## Database Schema

### Tables

#### projects
- `id` - Primary key
- `name` - Project name (unique)
- `repository_url` - Git repository URL
- `description` - Project description
- `language` - Primary programming language
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

#### reviews
- `id` - Primary key
- `project_id` - Foreign key to projects
- `commit_sha` - Git commit SHA
- `branch` - Git branch name
- `pr_number` - Pull request number
- `author` - Review author
- `started_at` - Review start time
- `completed_at` - Review completion time
- `duration_seconds` - Review duration
- `files_reviewed` - Number of files reviewed
- `total_findings` - Total number of findings
- `critical_findings` - Number of critical findings
- `high_findings` - Number of high severity findings
- `medium_findings` - Number of medium severity findings
- `low_findings` - Number of low severity findings
- `info_findings` - Number of info findings
- `provider` - AI provider used
- `model` - AI model used
- `total_tokens` - Total tokens used
- `total_cost` - Total cost
- `status` - Review status (pending, running, completed, failed)

#### findings
- `id` - Primary key
- `review_id` - Foreign key to reviews
- `type` - Finding type (security, performance, style, etc.)
- `severity` - Severity level (critical, high, medium, low, info)
- `category` - Finding category
- `file_path` - File path
- `line_start` - Start line number
- `line_end` - End line number
- `message` - Finding message
- `suggestion` - Suggested fix
- `code_snippet` - Code snippet
- `confidence` - Confidence score (0.0-1.0)
- `status` - Finding status (open, fixed, ignored, false_positive)
- `fixed_at` - Fix timestamp
- `fixed_by` - User who fixed it
- `fixed_in_commit` - Commit where it was fixed

#### project_metrics
- `id` - Primary key
- `project_id` - Foreign key to projects
- `recorded_at` - Metric recording time
- `total_lines` - Total lines of code
- `total_files` - Total number of files
- `total_issues` - Total issues
- `critical_issues` - Critical issues
- `high_issues` - High severity issues
- `medium_issues` - Medium severity issues
- `low_issues` - Low severity issues
- `security_score` - Security score (0-100)
- `performance_score` - Performance score (0-100)
- `maintainability_score` - Maintainability score (0-100)
- `overall_score` - Overall quality score (0-100)
- `custom_metrics` - Additional metrics (JSON)

---

## Integration

### CI/CD Integration

#### GitHub Actions

```yaml
name: Code Review with Dashboard
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run reviewr
        run: |
          reviewr src/ --all --output-format json > results.json
      
      - name: Send to Dashboard
        run: |
          python scripts/send_to_dashboard.py results.json
        env:
          DASHBOARD_URL: ${{ secrets.DASHBOARD_URL }}
```

#### GitLab CI

```yaml
code_review:
  script:
    - reviewr src/ --all --output-format json > results.json
    - python scripts/send_to_dashboard.py results.json
  variables:
    DASHBOARD_URL: $DASHBOARD_URL
```

### Python Integration

```python
from reviewr.dashboard.database import DatabaseManager
from reviewr.providers.base import ReviewFinding

# Initialize
db = DatabaseManager("sqlite:///reviewr.db")

# Create review
review = db.add_review(
    project_name="my-app",
    commit_sha="abc123",
    provider="claude"
)

# Add findings
for finding in findings:
    db.add_finding(
        review_id=review.id,
        type=finding.type.value,
        severity=finding.severity,
        file_path=finding.file_path,
        line_start=finding.line_start,
        line_end=finding.line_end,
        message=finding.message
    )
```

---

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY reviewr/ reviewr/

EXPOSE 8000

CMD ["uvicorn", "reviewr.dashboard.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t reviewr-dashboard .
docker run -p 8000:8000 -v $(pwd)/data:/app/data reviewr-dashboard
```

### Production Deployment

1. **Use PostgreSQL**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/reviewr"
   ```

2. **Add Authentication**
   - Implement JWT authentication
   - Add user management
   - Configure CORS properly

3. **Use Reverse Proxy**
   ```nginx
   server {
       listen 80;
       server_name dashboard.example.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **Enable HTTPS**
   ```bash
   certbot --nginx -d dashboard.example.com
   ```

---

## Troubleshooting

### Issue: "Database is locked"

**Cause:** SQLite doesn't handle concurrent writes well

**Solution:** Use PostgreSQL for production or reduce concurrent access

### Issue: "Module not found"

**Cause:** Missing dependencies

**Solution:**
```bash
pip install fastapi uvicorn sqlalchemy
```

### Issue: "Port already in use"

**Cause:** Another process is using port 8000

**Solution:**
```bash
# Use different port
reviewr dashboard start --port 8080

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

### Issue: "CORS errors"

**Cause:** Frontend and backend on different domains

**Solution:** Configure CORS in `api.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

**Built by world-class engineers** 🌟

**Status:** ✅ Production Ready


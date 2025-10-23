# reviewr Web Dashboard Integration Guide

## Overview

The **reviewr Web Dashboard** provides a comprehensive web-based interface for visualizing code review data, tracking trends, and monitoring code quality metrics across projects. It features a RESTful API, real-time metrics, and historical trend analysis.

## Features

 **Historical Review Data** - Store and query all review results 
 **Trend Analysis** - Visualize code quality trends over time 
 **Team Metrics** - Track team performance and productivity 
 **Cost Tracking** - Monitor API usage and costs 
 **Quality Gates** - Define and enforce quality thresholds 
 **RESTful API** - Integrate with external tools and services 
 **Real-time Metrics** - Live dashboard updates 
 **Multi-Project Support** - Manage multiple projects in one dashboard

## Quick Start

### 1. Initialize the Database

```bash
# Initialize database with default SQLite
reviewr dashboard init-db

# Or use PostgreSQL
reviewr dashboard init-db --database-url postgresql://user:pass@localhost/reviewr
```

### 2. Start the Dashboard Server

```bash
# Start with default settings
reviewr dashboard start

# Start on custom port
reviewr dashboard start --port 8080

# Start in development mode with auto-reload
reviewr dashboard start --reload
```

The dashboard will be available at:
- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. Add a Project

```bash
# Add a project
reviewr dashboard add-project my-app \
 --repository-url https://github.com/user/my-app \
 --language python \
 --description "My awesome application"

# List all projects
reviewr dashboard list-projects
```

### 4. Upload Review Results

```bash
# Run a review and save results
reviewr /path/to/code --output results.json

# Upload results to dashboard
reviewr dashboard upload results.json \
 --project-name my-app \
 --commit-sha abc123 \
 --branch main \
 --author "John Doe"
```

### 5. View Statistics

```bash
# Show dashboard statistics
reviewr dashboard stats
```

## Configuration

### Database Configuration

The dashboard supports multiple database backends:

#### SQLite (Default)

```bash
export REVIEWR_DATABASE_URL="sqlite:///./reviewr_dashboard.db"
```

#### PostgreSQL (Recommended for Production)

```bash
export REVIEWR_DATABASE_URL="postgresql://user:password@localhost:5432/reviewr"
```

#### MySQL

```bash
export REVIEWR_DATABASE_URL="mysql+pymysql://user:password@localhost:3306/reviewr"
```

### Environment Variables

```bash
# Database URL
export REVIEWR_DATABASE_URL="sqlite:///./reviewr_dashboard.db"

# Enable SQL query logging (for debugging)
export REVIEWR_DB_ECHO="true"

# Server host and port
export REVIEWR_DASHBOARD_HOST="0.0.0.0"
export REVIEWR_DASHBOARD_PORT="8000"
```

## CLI Commands

### `reviewr dashboard start`

Start the web dashboard server.

**Options:**
- `--host` - Host to bind to (default: 0.0.0.0)
- `--port` - Port to bind to (default: 8000)
- `--reload` - Enable auto-reload for development
- `--database-url` - Database URL

**Examples:**

```bash
# Start with defaults
reviewr dashboard start

# Start on custom port
reviewr dashboard start --port 8080

# Development mode with auto-reload
reviewr dashboard start --reload

# Use PostgreSQL
reviewr dashboard start --database-url postgresql://user:pass@localhost/reviewr
```

### `reviewr dashboard init-db`

Initialize the dashboard database.

**Options:**
- `--database-url` - Database URL
- `--drop` - Drop existing tables first (WARNING: deletes all data)

**Examples:**

```bash
# Initialize database
reviewr dashboard init-db

# Drop and recreate tables
reviewr dashboard init-db --drop

# Use PostgreSQL
reviewr dashboard init-db --database-url postgresql://user:pass@localhost/reviewr
```

### `reviewr dashboard add-project`

Add a new project to the dashboard.

**Arguments:**
- `name` - Project name (required)

**Options:**
- `--repository-url` - Repository URL
- `--description` - Project description
- `--language` - Primary programming language
- `--database-url` - Database URL

**Examples:**

```bash
# Add a simple project
reviewr dashboard add-project my-app

# Add with full details
reviewr dashboard add-project my-app \
 --repository-url https://github.com/user/my-app \
 --language python \
 --description "My awesome application"
```

### `reviewr dashboard list-projects`

List all projects in the dashboard.

**Options:**
- `--database-url` - Database URL

**Examples:**

```bash
# List all projects
reviewr dashboard list-projects
```

### `reviewr dashboard stats`

Show dashboard statistics.

**Options:**
- `--database-url` - Database URL

**Examples:**

```bash
# Show statistics
reviewr dashboard stats
```

### `reviewr dashboard upload`

Upload review results to the dashboard.

**Arguments:**
- `results_file` - Path to review results JSON file (required)

**Options:**
- `--project-name` - Project name (required)
- `--commit-sha` - Commit SHA
- `--branch` - Branch name
- `--author` - Author name
- `--database-url` - Database URL

**Examples:**

```bash
# Upload results
reviewr dashboard upload results.json --project-name my-app

# Upload with full metadata
reviewr dashboard upload results.json \
 --project-name my-app \
 --commit-sha abc123def456 \
 --branch main \
 --author "John Doe"
```

## API Endpoints

The dashboard provides a RESTful API for integration with external tools.

### Projects

- `POST /api/projects` - Create a new project
- `GET /api/projects` - List all projects
- `GET /api/projects/{id}` - Get a specific project

### Reviews

- `POST /api/reviews` - Create a new review
- `GET /api/reviews` - List reviews (with optional project filter)
- `GET /api/reviews/{id}` - Get a specific review
- `PATCH /api/reviews/{id}` - Update a review

### Findings

- `POST /api/findings` - Create a new finding
- `GET /api/findings` - List findings (with optional filters)

### Metrics

- `GET /api/metrics/overview` - Get overview metrics
- `GET /api/metrics/trends/{project_id}` - Get trend data for a project

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## CI/CD Integration

### GitHub Actions

```yaml
name: Code Review with Dashboard

on: [push, pull_request]

jobs:
 review:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v3
 
 - name: Run reviewr
 run: |
 pip install reviewr
 reviewr . --output results.json
 
 - name: Upload to Dashboard
 run: |
 reviewr dashboard upload results.json \
 --project-name ${{ github.repository }} \
 --commit-sha ${{ github.sha }} \
 --branch ${{ github.ref_name }} \
 --author "${{ github.actor }}" \
 --database-url ${{ secrets.REVIEWR_DATABASE_URL }}
```

### GitLab CI

```yaml
code_review:
 script:
 - pip install reviewr
 - reviewr . --output results.json
 - |
 reviewr dashboard upload results.json \
 --project-name $CI_PROJECT_NAME \
 --commit-sha $CI_COMMIT_SHA \
 --branch $CI_COMMIT_BRANCH \
 --author "$CI_COMMIT_AUTHOR" \
 --database-url $REVIEWR_DATABASE_URL
```

## Docker Deployment

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
 postgres:
 image: postgres:15
 environment:
 POSTGRES_DB: reviewr
 POSTGRES_USER: reviewr
 POSTGRES_PASSWORD: reviewr_password
 volumes:
 - postgres_data:/var/lib/postgresql/data
 ports:
 - "5432:5432"

 dashboard:
 image: reviewr:latest
 command: reviewr dashboard start --host 0.0.0.0 --port 8000
 environment:
 REVIEWR_DATABASE_URL: postgresql://reviewr:reviewr_password@postgres:5432/reviewr
 ports:
 - "8000:8000"
 depends_on:
 - postgres

volumes:
 postgres_data:
```

Start the services:

```bash
docker-compose up -d
```

## Best Practices

1. **Use PostgreSQL for Production** - SQLite is great for development, but PostgreSQL is recommended for production deployments.

2. **Regular Backups** - Back up your database regularly to prevent data loss.

3. **Monitor Disk Space** - The database can grow large over time. Monitor disk space and implement data retention policies.

4. **Secure the API** - In production, implement authentication and authorization for the API endpoints.

5. **Use Environment Variables** - Store sensitive configuration (database URLs, API keys) in environment variables, not in code.

6. **Enable HTTPS** - Use a reverse proxy (nginx, Caddy) to enable HTTPS for the dashboard.

## Troubleshooting

### Database Connection Errors

```bash
# Test database connection
python3 -c "from reviewr.dashboard.database import DatabaseManager; dm = DatabaseManager(); print('Connection OK' if dm.check_connection() else 'Connection Failed')"
```

### Port Already in Use

```bash
# Use a different port
reviewr dashboard start --port 8080
```

### Missing Dependencies

```bash
# Install dashboard dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary
```

## Next Steps

- Explore the API documentation at http://localhost:8000/docs
- Set up automated uploads from your CI/CD pipeline
- Configure quality gates for your projects
- Create custom reports and dashboards

## Support

For issues and questions:
- GitHub Issues: https://github.com/user/reviewr/issues
- Documentation: README.md
"""
FastAPI backend for reviewr web dashboard.

This module provides REST API endpoints for storing and retrieving
code review data, metrics, and analytics.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from .database import (
    DatabaseManager,
    Project,
    Review,
    Finding,
    ProjectMetric,
    User
)

# Initialize FastAPI app
app = FastAPI(
    title="reviewr Dashboard API",
    description="REST API for reviewr code review dashboard",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database manager
db_manager = DatabaseManager()

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include advanced metrics router
try:
    from .api_metrics import router as metrics_router
    app.include_router(metrics_router)
except ImportError:
    pass  # Metrics module not available


# Pydantic models for API
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    repository_url: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    repository_url: Optional[str]
    description: Optional[str]
    language: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    project_name: str
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    pr_number: Optional[int] = None
    author: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    project_id: int
    commit_sha: Optional[str]
    branch: Optional[str]
    pr_number: Optional[int]
    author: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    files_reviewed: int
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    info_findings: int
    provider: Optional[str]
    model: Optional[str]
    status: str
    
    class Config:
        from_attributes = True


class FindingCreate(BaseModel):
    review_id: int
    type: str
    severity: str
    category: Optional[str] = None
    file_path: str
    line_start: int
    line_end: int
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    confidence: Optional[float] = None


class FindingResponse(BaseModel):
    id: int
    review_id: int
    type: str
    severity: str
    category: Optional[str]
    file_path: str
    line_start: int
    line_end: int
    message: str
    suggestion: Optional[str]
    code_snippet: Optional[str]
    confidence: Optional[float]
    status: str
    
    class Config:
        from_attributes = True


class MetricsResponse(BaseModel):
    total_projects: int
    total_reviews: int
    total_findings: int
    avg_findings_per_review: float
    critical_findings: int
    high_findings: int


class TrendData(BaseModel):
    date: str
    value: float


class ProjectTrendsResponse(BaseModel):
    total_issues: List[TrendData]
    critical_issues: List[TrendData]
    overall_score: List[TrendData]


# Dependency to get database session
def get_db():
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    db_manager.create_tables()


@app.get("/")
async def root():
    """Serve the dashboard HTML."""
    index_path = Path(__file__).parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "name": "reviewr Dashboard API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Project endpoints

@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    # Check if project already exists
    existing = db.query(Project).filter_by(name=project.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project already exists")
    
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@app.get("/api/projects", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List all projects."""
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects


@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project."""
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# Review endpoints

@app.post("/api/reviews", response_model=ReviewResponse)
async def create_review(review: ReviewCreate, db: Session = Depends(get_db)):
    """Create a new review."""
    # Get or create project
    project = db.query(Project).filter_by(name=review.project_name).first()
    if not project:
        project = Project(name=review.project_name)
        db.add(project)
        db.flush()
    
    db_review = Review(
        project_id=project.id,
        commit_sha=review.commit_sha,
        branch=review.branch,
        pr_number=review.pr_number,
        author=review.author,
        provider=review.provider,
        model=review.model,
        status='running'
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@app.get("/api/reviews", response_model=List[ReviewResponse])
async def list_reviews(
    project_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List reviews, optionally filtered by project."""
    query = db.query(Review)
    if project_id:
        query = query.filter_by(project_id=project_id)
    
    reviews = query.order_by(desc(Review.started_at)).offset(skip).limit(limit).all()
    return reviews


@app.get("/api/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get a specific review."""
    review = db.query(Review).filter_by(id=review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@app.patch("/api/reviews/{review_id}")
async def update_review(
    review_id: int,
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update a review."""
    review = db.query(Review).filter_by(id=review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    for key, value in updates.items():
        if hasattr(review, key):
            setattr(review, key, value)
    
    db.commit()
    db.refresh(review)
    return review


# Finding endpoints

@app.post("/api/findings", response_model=FindingResponse)
async def create_finding(finding: FindingCreate, db: Session = Depends(get_db)):
    """Create a new finding."""
    # Verify review exists
    review = db.query(Review).filter_by(id=finding.review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    db_finding = Finding(**finding.dict())
    db.add(db_finding)
    
    # Update review statistics
    review.total_findings += 1
    if finding.severity == 'critical':
        review.critical_findings += 1
    elif finding.severity == 'high':
        review.high_findings += 1
    elif finding.severity == 'medium':
        review.medium_findings += 1
    elif finding.severity == 'low':
        review.low_findings += 1
    elif finding.severity == 'info':
        review.info_findings += 1
    
    db.commit()
    db.refresh(db_finding)
    return db_finding


@app.get("/api/findings", response_model=List[FindingResponse])
async def list_findings(
    review_id: Optional[int] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List findings with optional filters."""
    query = db.query(Finding)
    
    if review_id:
        query = query.filter_by(review_id=review_id)
    if severity:
        query = query.filter_by(severity=severity)
    if status:
        query = query.filter_by(status=status)
    
    findings = query.offset(skip).limit(limit).all()
    return findings


# Analytics endpoints

@app.get("/api/metrics/overview", response_model=MetricsResponse)
async def get_overview_metrics(db: Session = Depends(get_db)):
    """Get overview metrics across all projects."""
    total_projects = db.query(func.count(Project.id)).scalar()
    total_reviews = db.query(func.count(Review.id)).scalar()
    total_findings = db.query(func.count(Finding.id)).scalar()
    
    avg_findings = db.query(func.avg(Review.total_findings)).scalar() or 0.0
    
    critical = db.query(func.sum(Review.critical_findings)).scalar() or 0
    high = db.query(func.sum(Review.high_findings)).scalar() or 0
    
    return MetricsResponse(
        total_projects=total_projects,
        total_reviews=total_reviews,
        total_findings=total_findings,
        avg_findings_per_review=float(avg_findings),
        critical_findings=critical,
        high_findings=high
    )


@app.get("/api/metrics/trends/{project_id}", response_model=ProjectTrendsResponse)
async def get_project_trends(
    project_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get trend data for a project."""
    # Get reviews from the last N days
    since = datetime.utcnow() - timedelta(days=days)
    
    reviews = (
        db.query(Review)
        .filter(Review.project_id == project_id)
        .filter(Review.started_at >= since)
        .order_by(Review.started_at)
        .all()
    )
    
    # Aggregate by date
    total_issues = []
    critical_issues = []
    
    for review in reviews:
        date_str = review.started_at.strftime("%Y-%m-%d")
        total_issues.append(TrendData(date=date_str, value=float(review.total_findings)))
        critical_issues.append(TrendData(date=date_str, value=float(review.critical_findings)))
    
    # Calculate overall score (simple formula: 100 - (critical*10 + high*5 + medium*2))
    overall_score = []
    for review in reviews:
        date_str = review.started_at.strftime("%Y-%m-%d")
        score = max(0, 100 - (review.critical_findings * 10 + review.high_findings * 5 + review.medium_findings * 2))
        overall_score.append(TrendData(date=date_str, value=float(score)))
    
    return ProjectTrendsResponse(
        total_issues=total_issues,
        critical_issues=critical_issues,
        overall_score=overall_score
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


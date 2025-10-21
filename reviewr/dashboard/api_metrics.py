"""
Advanced metrics API endpoints for reviewr dashboard.

This module provides REST API endpoints for trend analysis, quality gates,
technical debt tracking, and team performance metrics.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import statistics
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel, Field

from .database import DatabaseManager
from .models import (
    Project, Review, Finding, TrendSnapshot, TechnicalDebtItem,
    TeamMetrics, QualityGate, QualityGateEvaluation
)


# Initialize router
router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Database dependency
def get_db():
    """Get database session."""
    db_manager = DatabaseManager()
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


# Pydantic models for API
class TrendSnapshotCreate(BaseModel):
    project_id: int


class TrendSnapshotResponse(BaseModel):
    date: datetime
    total_findings: int
    severity_breakdown: Dict[str, int]
    technical_debt_hours: float
    code_quality_score: float
    files_analyzed: int
    lines_of_code: int


class QualityGateCreate(BaseModel):
    project_id: int
    name: str
    enabled: bool = True
    max_critical: int = 0
    max_high: int = 5
    max_medium: int = 20
    max_technical_debt_hours: float = 40.0
    min_code_quality_score: float = 70.0


class TechnicalDebtItemCreate(BaseModel):
    project_id: int
    finding_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    estimated_hours: float = 0.0
    priority: str = 'medium'
    status: str = 'open'
    assigned_to: Optional[str] = None


# Helper functions
def calculate_trend(values: List[float]) -> str:
    """Calculate trend direction (improving, stable, declining)."""
    if len(values) < 2:
        return "stable"
    
    # Linear regression
    n = len(values)
    x = list(range(n))
    
    try:
        slope = (n * sum(x[i] * values[i] for i in range(n)) - sum(x) * sum(values)) / \
                (n * sum(x[i]**2 for i in range(n)) - sum(x)**2)
        
        if slope < -0.1:
            return "improving"
        elif slope > 0.1:
            return "declining"
        else:
            return "stable"
    except ZeroDivisionError:
        return "stable"


def calculate_improvement_rate(snapshots: List[TrendSnapshot]) -> float:
    """Calculate improvement rate as percentage."""
    if len(snapshots) < 2:
        return 0.0
    
    first = snapshots[0].total_findings
    last = snapshots[-1].total_findings
    
    if first == 0:
        return 0.0
    
    return ((first - last) / first) * 100


def calculate_technical_debt(findings: List[Finding]) -> float:
    """Calculate technical debt in hours."""
    debt_map = {
        'critical': 8.0,
        'high': 4.0,
        'medium': 2.0,
        'low': 1.0,
        'info': 0.5
    }
    
    return sum(debt_map.get(f.severity, 0) for f in findings)


def calculate_quality_score(findings: List[Finding], files_count: int) -> float:
    """Calculate code quality score (0-100)."""
    if files_count == 0:
        return 100.0
    
    # Weight findings by severity
    weighted_findings = sum(
        10 if f.severity == 'critical' else
        5 if f.severity == 'high' else
        2 if f.severity == 'medium' else
        1 if f.severity == 'low' else 0.5
        for f in findings
    )
    
    # Calculate score (100 - penalty per file)
    penalty_per_file = weighted_findings / files_count
    score = max(0, 100 - penalty_per_file * 10)
    
    return round(score, 2)


def calculate_loc(project_id: int, db: Session) -> int:
    """Calculate lines of code for a project."""
    # This is a placeholder - in production, you'd integrate with git or cloc
    latest_review = db.query(Review).filter(
        Review.project_id == project_id
    ).order_by(Review.created_at.desc()).first()
    
    return latest_review.total_lines if latest_review else 0


# Trend Analysis Endpoints
@router.get("/trends/{project_id}")
async def get_trends(
    project_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get trend data for a project over the specified number of days."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    snapshots = db.query(TrendSnapshot).filter(
        TrendSnapshot.project_id == project_id,
        TrendSnapshot.snapshot_date >= start_date,
        TrendSnapshot.snapshot_date <= end_date
    ).order_by(TrendSnapshot.snapshot_date).all()
    
    if not snapshots:
        return {
            "project_id": project_id,
            "period": {"start": start_date, "end": end_date},
            "snapshots": [],
            "summary": {
                "avg_findings": 0,
                "trend": "stable",
                "improvement_rate": 0.0
            }
        }
    
    return {
        "project_id": project_id,
        "period": {"start": start_date, "end": end_date},
        "snapshots": [
            {
                "date": s.snapshot_date,
                "total_findings": s.total_findings,
                "severity_breakdown": {
                    "critical": s.critical_count,
                    "high": s.high_count,
                    "medium": s.medium_count,
                    "low": s.low_count,
                    "info": s.info_count
                },
                "technical_debt_hours": s.technical_debt_hours,
                "code_quality_score": s.code_quality_score,
                "files_analyzed": s.files_analyzed,
                "lines_of_code": s.lines_of_code
            }
            for s in snapshots
        ],
        "summary": {
            "avg_findings": statistics.mean([s.total_findings for s in snapshots]),
            "trend": calculate_trend([s.total_findings for s in snapshots]),
            "improvement_rate": calculate_improvement_rate(snapshots)
        }
    }


@router.post("/trends/{project_id}/snapshot")
async def create_snapshot(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Create a new trend snapshot for a project."""
    # Get latest review
    latest_review = db.query(Review).filter(
        Review.project_id == project_id
    ).order_by(Review.created_at.desc()).first()
    
    if not latest_review:
        raise HTTPException(status_code=404, detail="No reviews found for project")
    
    # Get findings
    findings = db.query(Finding).filter(
        Finding.review_id == latest_review.id
    ).all()
    
    # Create snapshot
    snapshot = TrendSnapshot(
        project_id=project_id,
        snapshot_date=datetime.now(),
        total_findings=len(findings),
        critical_count=sum(1 for f in findings if f.severity == 'critical'),
        high_count=sum(1 for f in findings if f.severity == 'high'),
        medium_count=sum(1 for f in findings if f.severity == 'medium'),
        low_count=sum(1 for f in findings if f.severity == 'low'),
        info_count=sum(1 for f in findings if f.severity == 'info'),
        files_analyzed=latest_review.total_files,
        lines_of_code=calculate_loc(project_id, db),
        technical_debt_hours=calculate_technical_debt(findings),
        code_quality_score=calculate_quality_score(findings, latest_review.total_files)
    )
    
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    return {"status": "success", "snapshot_id": snapshot.id, "snapshot_date": snapshot.snapshot_date}


# Quality Gates Endpoints
@router.post("/quality-gates")
async def create_quality_gate(
    gate: QualityGateCreate,
    db: Session = Depends(get_db)
):
    """Create a new quality gate."""
    db_gate = QualityGate(
        project_id=gate.project_id,
        name=gate.name,
        is_active=gate.enabled,
        max_critical_findings=gate.max_critical,
        max_high_findings=gate.max_high,
        max_medium_findings=gate.max_medium,
        max_technical_debt_minutes=int(gate.max_technical_debt_hours * 60),
        min_maintainability_index=gate.min_code_quality_score
    )
    db.add(db_gate)
    db.commit()
    db.refresh(db_gate)
    return db_gate


@router.get("/quality-gates/{project_id}")
async def get_quality_gates(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get all quality gates for a project."""
    gates = db.query(QualityGate).filter(
        QualityGate.project_id == project_id
    ).all()
    return gates


@router.post("/quality-gates/{gate_id}/check/{review_id}")
async def check_quality_gate(
    gate_id: int,
    review_id: int,
    db: Session = Depends(get_db)
):
    """Check if a review passes the quality gate."""
    gate = db.query(QualityGate).filter(QualityGate.id == gate_id).first()
    if not gate:
        raise HTTPException(status_code=404, detail="Quality gate not found")
    
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    findings = db.query(Finding).filter(Finding.review_id == review_id).all()
    
    violations = []
    
    # Check severity thresholds
    if review.critical_count > gate.max_critical_findings:
        violations.append({
            "type": "critical_findings",
            "threshold": gate.max_critical_findings,
            "actual": review.critical_count
        })
    
    if review.high_count > gate.max_high_findings:
        violations.append({
            "type": "high_findings",
            "threshold": gate.max_high_findings,
            "actual": review.high_count
        })
    
    if review.medium_count > gate.max_medium_findings:
        violations.append({
            "type": "medium_findings",
            "threshold": gate.max_medium_findings,
            "actual": review.medium_count
        })
    
    # Check technical debt
    tech_debt_hours = calculate_technical_debt(findings)
    max_debt_hours = gate.max_technical_debt_minutes / 60.0
    if tech_debt_hours > max_debt_hours:
        violations.append({
            "type": "technical_debt",
            "threshold": max_debt_hours,
            "actual": tech_debt_hours
        })
    
    # Check code quality score
    quality_score = calculate_quality_score(findings, review.total_files)
    if quality_score < gate.min_maintainability_index:
        violations.append({
            "type": "code_quality_score",
            "threshold": gate.min_maintainability_index,
            "actual": quality_score
        })
    
    # Record evaluation
    evaluation = QualityGateEvaluation(
        quality_gate_id=gate_id,
        review_id=review_id,
        passed=len(violations) == 0,
        score=quality_score,
        failed_checks=violations if violations else None
    )
    db.add(evaluation)
    db.commit()
    
    return {
        "passed": len(violations) == 0,
        "violations": violations,
        "gate_name": gate.name,
        "quality_score": quality_score
    }


# Technical Debt Endpoints
@router.get("/technical-debt/{project_id}")
async def get_technical_debt(
    project_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get technical debt items for a project."""
    query = db.query(TechnicalDebtItem).filter(
        TechnicalDebtItem.project_id == project_id
    )

    if status:
        query = query.filter(TechnicalDebtItem.status == status)

    items = query.order_by(TechnicalDebtItem.priority.desc()).all()

    total_hours = sum(item.estimated_hours for item in items)

    return {
        "items": items,
        "summary": {
            "total_items": len(items),
            "total_hours": total_hours,
            "by_priority": {
                "critical": sum(1 for i in items if i.priority == 'critical'),
                "high": sum(1 for i in items if i.priority == 'high'),
                "medium": sum(1 for i in items if i.priority == 'medium'),
                "low": sum(1 for i in items if i.priority == 'low')
            },
            "by_status": {
                "open": sum(1 for i in items if i.status == 'open'),
                "in_progress": sum(1 for i in items if i.status == 'in_progress'),
                "resolved": sum(1 for i in items if i.status == 'resolved')
            }
        }
    }


@router.post("/technical-debt")
async def create_technical_debt_item(
    item: TechnicalDebtItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new technical debt item."""
    db_item = TechnicalDebtItem(
        project_id=item.project_id,
        finding_id=item.finding_id,
        title=item.title,
        description=item.description,
        estimated_hours=item.estimated_hours,
        priority=item.priority,
        status=item.status,
        assigned_to=item.assigned_to
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/technical-debt/{item_id}")
async def update_technical_debt_item(
    item_id: int,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    estimated_hours: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Update a technical debt item."""
    item = db.query(TechnicalDebtItem).filter(TechnicalDebtItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Technical debt item not found")

    if status:
        item.status = status
        if status == 'resolved':
            item.resolved_at = datetime.now()

    if assigned_to is not None:
        item.assigned_to = assigned_to

    if estimated_hours is not None:
        item.estimated_hours = estimated_hours

    db.commit()
    db.refresh(item)
    return item


# Team Metrics Endpoints
@router.get("/team-metrics/{project_id}")
async def get_team_metrics(
    project_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get team performance metrics for a project."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    metrics = db.query(TeamMetrics).filter(
        TeamMetrics.project_id == project_id,
        TeamMetrics.period_start >= start_date,
        TeamMetrics.period_end <= end_date
    ).all()

    # Aggregate by author
    author_stats = {}
    for metric in metrics:
        if metric.author not in author_stats:
            author_stats[metric.author] = {
                "author": metric.author,
                "commits": 0,
                "lines_added": 0,
                "lines_removed": 0,
                "findings_introduced": 0,
                "findings_fixed": 0,
                "avg_quality_score": []
            }

        author_stats[metric.author]["commits"] += metric.commits_count
        author_stats[metric.author]["lines_added"] += metric.lines_added
        author_stats[metric.author]["lines_removed"] += metric.lines_removed
        author_stats[metric.author]["findings_introduced"] += metric.findings_introduced
        author_stats[metric.author]["findings_fixed"] += metric.findings_fixed
        author_stats[metric.author]["avg_quality_score"].append(metric.code_quality_score)

    # Calculate averages
    for author in author_stats:
        scores = author_stats[author]["avg_quality_score"]
        author_stats[author]["avg_quality_score"] = statistics.mean(scores) if scores else 0.0

    return {
        "project_id": project_id,
        "period": {"start": start_date, "end": end_date},
        "team_stats": list(author_stats.values())
    }


@router.get("/dashboard-summary/{project_id}")
async def get_dashboard_summary(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard summary for a project."""
    # Get latest review
    latest_review = db.query(Review).filter(
        Review.project_id == project_id
    ).order_by(Review.created_at.desc()).first()

    if not latest_review:
        raise HTTPException(status_code=404, detail="No reviews found for project")

    # Get findings
    findings = db.query(Finding).filter(
        Finding.review_id == latest_review.id
    ).all()

    # Get technical debt
    debt_items = db.query(TechnicalDebtItem).filter(
        TechnicalDebtItem.project_id == project_id,
        TechnicalDebtItem.status != 'resolved'
    ).all()

    # Get trend (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    snapshots = db.query(TrendSnapshot).filter(
        TrendSnapshot.project_id == project_id,
        TrendSnapshot.snapshot_date >= thirty_days_ago
    ).order_by(TrendSnapshot.snapshot_date).all()

    return {
        "project_id": project_id,
        "latest_review": {
            "id": latest_review.id,
            "date": latest_review.started_at,
            "total_findings": latest_review.total_findings,
            "critical": latest_review.critical_count,
            "high": latest_review.high_count,
            "medium": latest_review.medium_count,
            "low": latest_review.low_count,
            "info": latest_review.info_count
        },
        "quality_score": calculate_quality_score(findings, latest_review.total_files),
        "technical_debt": {
            "total_items": len(debt_items),
            "total_hours": sum(item.estimated_hours for item in debt_items),
            "by_priority": {
                "critical": sum(1 for i in debt_items if i.priority == 'critical'),
                "high": sum(1 for i in debt_items if i.priority == 'high'),
                "medium": sum(1 for i in debt_items if i.priority == 'medium'),
                "low": sum(1 for i in debt_items if i.priority == 'low')
            }
        },
        "trend": {
            "direction": calculate_trend([s.total_findings for s in snapshots]) if snapshots else "stable",
            "improvement_rate": calculate_improvement_rate(snapshots) if snapshots else 0.0
        }
    }


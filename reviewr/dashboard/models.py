"""
Database models for the reviewr dashboard.

This module defines SQLAlchemy models for storing review data, metrics,
and historical information in the dashboard database.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum


Base = declarative_base()


class SeverityLevel(str, PyEnum):
    """Severity levels for findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReviewStatus(str, PyEnum):
    """Status of a review."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base):
    """Project model for tracking repositories."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    repository_url = Column(String(512))
    description = Column(Text)
    language = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class Review(Base):
    """Review model for storing review results."""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    commit_sha = Column(String(40), index=True)
    branch = Column(String(255), index=True)
    author = Column(String(255))
    status = Column(String(20), default=ReviewStatus.PENDING.value, index=True)
    
    # Review metadata
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    review_type = Column(String(50))  # security, performance, etc.
    preset = Column(String(50))  # strict, balanced, quick
    
    # Findings summary
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)
    
    # Performance metrics
    duration_seconds = Column(Float)
    api_calls = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Additional data
    extra_data = Column(JSON)  # Store additional metadata as JSON
    
    # Relationships
    project = relationship("Project", back_populates="reviews")
    findings = relationship("Finding", back_populates="review", cascade="all, delete-orphan")
    metrics = relationship("ReviewMetrics", back_populates="review", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_project_started', 'project_id', 'started_at'),
        Index('idx_status_started', 'status', 'started_at'),
    )
    
    def __repr__(self):
        return f"<Review(id={self.id}, project_id={self.project_id}, status='{self.status}')>"


class Finding(Base):
    """Finding model for storing individual code review findings."""
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, index=True)
    
    # Finding details
    severity = Column(String(20), nullable=False, index=True)
    category = Column(String(100), index=True)  # security, performance, etc.
    rule_id = Column(String(100), index=True)
    title = Column(String(512), nullable=False)
    description = Column(Text)
    recommendation = Column(Text)
    
    # Location
    file_path = Column(String(512), nullable=False, index=True)
    line_start = Column(Integer)
    line_end = Column(Integer)
    column_start = Column(Integer)
    column_end = Column(Integer)
    
    # Code context
    code_snippet = Column(Text)
    
    # Status tracking
    is_fixed = Column(Boolean, default=False, index=True)
    is_false_positive = Column(Boolean, default=False, index=True)
    fixed_at = Column(DateTime)
    fixed_in_commit = Column(String(40))

    # Additional data
    extra_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    review = relationship("Review", back_populates="findings")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_review_severity', 'review_id', 'severity'),
        Index('idx_review_category', 'review_id', 'category'),
        Index('idx_file_severity', 'file_path', 'severity'),
    )
    
    def __repr__(self):
        return f"<Finding(id={self.id}, severity='{self.severity}', title='{self.title[:50]}')>"


class ReviewMetrics(Base):
    """Metrics model for storing detailed review metrics."""
    __tablename__ = "review_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, unique=True, index=True)
    
    # Code metrics
    cyclomatic_complexity_avg = Column(Float)
    cyclomatic_complexity_max = Column(Float)
    cognitive_complexity_avg = Column(Float)
    maintainability_index = Column(Float)
    code_duplication_percentage = Column(Float)
    
    # Security metrics
    security_score = Column(Float)  # 0-100
    vulnerabilities_found = Column(Integer, default=0)
    secrets_found = Column(Integer, default=0)
    
    # Quality metrics
    code_coverage_percentage = Column(Float)
    test_count = Column(Integer)
    documentation_percentage = Column(Float)
    
    # Performance metrics
    performance_score = Column(Float)  # 0-100
    performance_issues = Column(Integer, default=0)
    
    # Technical debt
    technical_debt_minutes = Column(Integer)  # Estimated time to fix all issues
    technical_debt_ratio = Column(Float)  # Debt / Total development time

    # Additional metrics
    extra_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    review = relationship("Review", back_populates="metrics")
    
    def __repr__(self):
        return f"<ReviewMetrics(id={self.id}, review_id={self.review_id})>"


class QualityGate(Base):
    """Quality gate model for defining quality thresholds."""
    __tablename__ = "quality_gates"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    
    # Thresholds
    max_critical_findings = Column(Integer, default=0)
    max_high_findings = Column(Integer, default=5)
    max_medium_findings = Column(Integer, default=20)
    min_security_score = Column(Float, default=80.0)
    min_maintainability_index = Column(Float, default=60.0)
    max_technical_debt_minutes = Column(Integer, default=480)  # 8 hours
    
    # Additional rules
    rules = Column(JSON)  # Store custom rules as JSON
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project")
    evaluations = relationship("QualityGateEvaluation", back_populates="quality_gate", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QualityGate(id={self.id}, name='{self.name}')>"


class QualityGateEvaluation(Base):
    """Quality gate evaluation results."""
    __tablename__ = "quality_gate_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    quality_gate_id = Column(Integer, ForeignKey("quality_gates.id"), nullable=False, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False, index=True)

    passed = Column(Boolean, nullable=False, index=True)
    score = Column(Float)  # Overall score 0-100

    # Detailed results
    failed_checks = Column(JSON)  # List of failed checks
    warnings = Column(JSON)  # List of warnings

    evaluated_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    quality_gate = relationship("QualityGate", back_populates="evaluations")
    review = relationship("Review")

    __table_args__ = (
        Index('idx_gate_review', 'quality_gate_id', 'review_id'),
    )

    def __repr__(self):
        return f"<QualityGateEvaluation(id={self.id}, passed={self.passed})>"


class TrendSnapshot(Base):
    """Trend snapshot model for time-series analysis."""
    __tablename__ = "trend_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    snapshot_date = Column(DateTime, nullable=False, index=True)

    # Finding counts
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)

    # Code metrics
    files_analyzed = Column(Integer, default=0)
    lines_of_code = Column(Integer, default=0)

    # Quality metrics
    technical_debt_hours = Column(Float, default=0.0)
    code_quality_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project")

    __table_args__ = (
        Index('idx_project_snapshot_date', 'project_id', 'snapshot_date'),
    )

    def __repr__(self):
        return f"<TrendSnapshot(id={self.id}, project_id={self.project_id}, date={self.snapshot_date})>"


class TechnicalDebtItem(Base):
    """Technical debt item model for tracking debt."""
    __tablename__ = "technical_debt_items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    finding_id = Column(Integer, ForeignKey("findings.id"), nullable=True, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text)
    estimated_hours = Column(Float, default=0.0)
    priority = Column(String(20), default='medium', index=True)  # critical, high, medium, low
    status = Column(String(20), default='open', index=True)  # open, in_progress, resolved
    assigned_to = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)

    # Relationships
    project = relationship("Project")
    finding = relationship("Finding")

    __table_args__ = (
        Index('idx_project_status', 'project_id', 'status'),
        Index('idx_project_priority', 'project_id', 'priority'),
    )

    def __repr__(self):
        return f"<TechnicalDebtItem(id={self.id}, title='{self.title[:30]}', status='{self.status}')>"


class TeamMetrics(Base):
    """Team metrics model for tracking team performance."""
    __tablename__ = "team_metrics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)

    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)

    # Activity metrics
    commits_count = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_removed = Column(Integer, default=0)

    # Quality metrics
    findings_introduced = Column(Integer, default=0)
    findings_fixed = Column(Integer, default=0)
    avg_fix_time_hours = Column(Float, default=0.0)
    code_quality_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project")

    __table_args__ = (
        Index('idx_project_author', 'project_id', 'author'),
        Index('idx_project_period', 'project_id', 'period_start', 'period_end'),
    )

    def __repr__(self):
        return f"<TeamMetrics(id={self.id}, author='{self.author}', project_id={self.project_id})>"


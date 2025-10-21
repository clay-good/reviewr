"""
Database models and schema for reviewr web dashboard.

This module provides SQLAlchemy models for storing code review data,
metrics, and project information.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
    JSON,
    Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class Project(Base):
    """Project model for tracking repositories."""
    
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    repository_url = Column(String(512))
    description = Column(Text)
    language = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviews = relationship('Review', back_populates='project', cascade='all, delete-orphan')
    metrics = relationship('ProjectMetric', back_populates='project', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"


class Review(Base):
    """Review model for storing code review results."""
    
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    commit_sha = Column(String(40), index=True)
    branch = Column(String(255))
    pr_number = Column(Integer, index=True)
    author = Column(String(255))
    
    # Review metadata
    started_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Review statistics
    files_reviewed = Column(Integer, default=0)
    lines_reviewed = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    info_findings = Column(Integer, default=0)
    
    # Provider information
    provider = Column(String(50))
    model = Column(String(100))
    total_tokens = Column(Integer)
    total_cost = Column(Float)
    
    # Status
    status = Column(String(50), default='pending', index=True)  # pending, running, completed, failed
    error_message = Column(Text)
    
    # Relationships
    project = relationship('Project', back_populates='reviews')
    findings = relationship('Finding', back_populates='review', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Review(id={self.id}, project_id={self.project_id}, commit='{self.commit_sha[:8]}')>"


class Finding(Base):
    """Finding model for storing individual code issues."""
    
    __tablename__ = 'findings'
    
    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey('reviews.id'), nullable=False, index=True)
    
    # Finding details
    type = Column(String(50), index=True)  # security, performance, style, etc.
    severity = Column(String(20), index=True)  # critical, high, medium, low, info
    category = Column(String(100), index=True)
    
    # Location
    file_path = Column(String(512), index=True)
    line_start = Column(Integer)
    line_end = Column(Integer)
    
    # Content
    message = Column(Text, nullable=False)
    suggestion = Column(Text)
    code_snippet = Column(Text)
    
    # Metadata
    confidence = Column(Float)
    metric_name = Column(String(100))
    metric_value = Column(Float)
    
    # Status tracking
    status = Column(String(50), default='open', index=True)  # open, fixed, ignored, false_positive
    fixed_at = Column(DateTime)
    fixed_by = Column(String(255))
    fixed_in_commit = Column(String(40))
    
    # Relationships
    review = relationship('Review', back_populates='findings')
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_finding_review_severity', 'review_id', 'severity'),
        Index('idx_finding_review_type', 'review_id', 'type'),
        Index('idx_finding_file_status', 'file_path', 'status'),
    )
    
    def __repr__(self):
        return f"<Finding(id={self.id}, type='{self.type}', severity='{self.severity}')>"


class ProjectMetric(Base):
    """Project metrics for tracking code quality over time."""
    
    __tablename__ = 'project_metrics'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    
    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Code metrics
    total_lines = Column(Integer)
    total_files = Column(Integer)
    
    # Issue metrics
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # Quality scores (0-100)
    security_score = Column(Float)
    performance_score = Column(Float)
    maintainability_score = Column(Float)
    overall_score = Column(Float)
    
    # Trends (compared to previous metric)
    issues_trend = Column(String(20))  # improving, stable, declining
    score_trend = Column(String(20))
    
    # Additional metrics as JSON
    custom_metrics = Column(JSON)
    
    # Relationships
    project = relationship('Project', back_populates='metrics')
    
    __table_args__ = (
        Index('idx_metric_project_time', 'project_id', 'recorded_at'),
    )
    
    def __repr__(self):
        return f"<ProjectMetric(id={self.id}, project_id={self.project_id}, score={self.overall_score})>"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(255))
    avatar_url = Column(String(512))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class DatabaseManager:
    """Manager for database operations."""
    
    def __init__(self, database_url: str = "sqlite:///reviewr.db"):
        """
        Initialize database manager.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        # Use StaticPool for SQLite to avoid threading issues
        if database_url.startswith('sqlite'):
            self.engine = create_engine(
                database_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(database_url)
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables."""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    def add_review(
        self,
        project_name: str,
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None,
        pr_number: Optional[int] = None,
        author: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> Review:
        """
        Add a new review to the database.
        
        Args:
            project_name: Name of the project
            commit_sha: Git commit SHA
            branch: Git branch name
            pr_number: Pull request number
            author: Review author
            provider: AI provider used
            **kwargs: Additional review attributes
            
        Returns:
            Created Review object
        """
        session = self.get_session()
        try:
            # Get or create project
            project = session.query(Project).filter_by(name=project_name).first()
            if not project:
                project = Project(name=project_name)
                session.add(project)
                session.flush()
            
            # Create review
            review = Review(
                project_id=project.id,
                commit_sha=commit_sha,
                branch=branch,
                pr_number=pr_number,
                author=author,
                provider=provider,
                **kwargs
            )
            session.add(review)
            session.commit()
            session.refresh(review)
            return review
        finally:
            session.close()
    
    def add_finding(self, review_id: int, **kwargs) -> Finding:
        """
        Add a finding to a review.
        
        Args:
            review_id: ID of the review
            **kwargs: Finding attributes
            
        Returns:
            Created Finding object
        """
        session = self.get_session()
        try:
            finding = Finding(review_id=review_id, **kwargs)
            session.add(finding)
            session.commit()
            session.refresh(finding)
            return finding
        finally:
            session.close()
    
    def get_project_reviews(self, project_name: str, limit: int = 50) -> List[Review]:
        """Get recent reviews for a project."""
        session = self.get_session()
        try:
            project = session.query(Project).filter_by(name=project_name).first()
            if not project:
                return []
            
            reviews = (
                session.query(Review)
                .filter_by(project_id=project.id)
                .order_by(Review.started_at.desc())
                .limit(limit)
                .all()
            )
            return reviews
        finally:
            session.close()
    
    def get_review_findings(self, review_id: int) -> List[Finding]:
        """Get all findings for a review."""
        session = self.get_session()
        try:
            findings = (
                session.query(Finding)
                .filter_by(review_id=review_id)
                .order_by(Finding.severity, Finding.file_path)
                .all()
            )
            return findings
        finally:
            session.close()


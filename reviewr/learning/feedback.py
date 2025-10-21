"""
Feedback collection and storage for learning mode.

Tracks user feedback on findings to improve accuracy over time.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json
import sqlite3
from enum import Enum


class FeedbackType(Enum):
    """Type of feedback."""
    ACCEPT = "accept"  # User agrees with finding
    REJECT = "reject"  # False positive
    MODIFY = "modify"  # Finding is partially correct
    SKIP = "skip"  # User skipped/ignored


class FeedbackReason(Enum):
    """Reason for feedback."""
    FALSE_POSITIVE = "false_positive"
    TOO_NOISY = "too_noisy"
    LOW_PRIORITY = "low_priority"
    ALREADY_KNOWN = "already_known"
    NOT_APPLICABLE = "not_applicable"
    INCORRECT_SEVERITY = "incorrect_severity"
    HELPFUL = "helpful"
    CRITICAL = "critical"
    OTHER = "other"


@dataclass
class FindingFeedback:
    """Feedback on a specific finding."""
    
    finding_id: str  # Hash of finding
    feedback_type: FeedbackType
    reason: Optional[FeedbackReason] = None
    comment: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Finding metadata
    rule_id: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    
    # Context
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Suggested changes
    suggested_severity: Optional[str] = None
    suggested_category: Optional[str] = None


class FeedbackStore:
    """Store and retrieve feedback data."""
    
    def __init__(self, db_path: Path):
        """
        Initialize feedback store.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_id TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                reason TEXT,
                comment TEXT,
                timestamp TEXT NOT NULL,
                rule_id TEXT,
                severity TEXT,
                category TEXT,
                file_path TEXT,
                line_number INTEGER,
                project_id TEXT,
                user_id TEXT,
                suggested_severity TEXT,
                suggested_category TEXT,
                UNIQUE(finding_id, timestamp)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_finding_id ON feedback(finding_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rule_id ON feedback(rule_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)
        """)
        
        conn.commit()
        conn.close()
    
    def add_feedback(self, feedback: FindingFeedback):
        """Add feedback to store."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO feedback (
                finding_id, feedback_type, reason, comment, timestamp,
                rule_id, severity, category, file_path, line_number,
                project_id, user_id, suggested_severity, suggested_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback.finding_id,
            feedback.feedback_type.value,
            feedback.reason.value if feedback.reason else None,
            feedback.comment,
            feedback.timestamp.isoformat(),
            feedback.rule_id,
            feedback.severity,
            feedback.category,
            feedback.file_path,
            feedback.line_number,
            feedback.project_id,
            feedback.user_id,
            feedback.suggested_severity,
            feedback.suggested_category
        ))
        
        conn.commit()
        conn.close()
    
    def get_feedback_for_finding(self, finding_id: str) -> List[FindingFeedback]:
        """Get all feedback for a specific finding."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM feedback WHERE finding_id = ? ORDER BY timestamp DESC
        """, (finding_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_feedback(row) for row in rows]
    
    def get_feedback_for_rule(self, rule_id: str) -> List[FindingFeedback]:
        """Get all feedback for a specific rule."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM feedback WHERE rule_id = ? ORDER BY timestamp DESC
        """, (rule_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_feedback(row) for row in rows]
    
    def get_feedback_stats(self, rule_id: Optional[str] = None) -> Dict[str, Any]:
        """Get feedback statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if rule_id:
            cursor.execute("""
                SELECT feedback_type, COUNT(*) as count
                FROM feedback
                WHERE rule_id = ?
                GROUP BY feedback_type
            """, (rule_id,))
        else:
            cursor.execute("""
                SELECT feedback_type, COUNT(*) as count
                FROM feedback
                GROUP BY feedback_type
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = {
            'accept': 0,
            'reject': 0,
            'modify': 0,
            'skip': 0,
            'total': 0
        }
        
        for feedback_type, count in rows:
            stats[feedback_type] = count
            stats['total'] += count
        
        if stats['total'] > 0:
            stats['accept_rate'] = stats['accept'] / stats['total']
            stats['reject_rate'] = stats['reject'] / stats['total']
        else:
            stats['accept_rate'] = 0.0
            stats['reject_rate'] = 0.0
        
        return stats
    
    def get_false_positive_rules(self, threshold: float = 0.5) -> List[str]:
        """
        Get rules with high false positive rate.
        
        Args:
            threshold: Minimum reject rate to consider (0.0-1.0)
            
        Returns:
            List of rule IDs with high false positive rate
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                rule_id,
                SUM(CASE WHEN feedback_type = 'reject' THEN 1 ELSE 0 END) as rejects,
                COUNT(*) as total
            FROM feedback
            WHERE rule_id IS NOT NULL
            GROUP BY rule_id
            HAVING (CAST(rejects AS FLOAT) / total) >= ?
        """, (threshold,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]
    
    def _row_to_feedback(self, row: tuple) -> FindingFeedback:
        """Convert database row to FindingFeedback."""
        return FindingFeedback(
            finding_id=row[1],
            feedback_type=FeedbackType(row[2]),
            reason=FeedbackReason(row[3]) if row[3] else None,
            comment=row[4],
            timestamp=datetime.fromisoformat(row[5]),
            rule_id=row[6],
            severity=row[7],
            category=row[8],
            file_path=row[9],
            line_number=row[10],
            project_id=row[11],
            user_id=row[12],
            suggested_severity=row[13],
            suggested_category=row[14]
        )
    
    def export_feedback(self, output_path: Path):
        """Export all feedback to JSON file."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM feedback ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        
        feedback_list = [self._row_to_feedback(row) for row in rows]
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'total_feedback': len(feedback_list),
            'feedback': [
                {
                    **asdict(fb),
                    'feedback_type': fb.feedback_type.value,
                    'reason': fb.reason.value if fb.reason else None,
                    'timestamp': fb.timestamp.isoformat()
                }
                for fb in feedback_list
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)


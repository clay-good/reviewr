"""
Learning model that adapts based on user feedback.

Uses feedback to:
- Adjust severity levels
- Filter false positives
- Customize rule priorities
- Learn team-specific patterns
"""

from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass, field
import json
from collections import defaultdict

from .feedback import FeedbackStore, FeedbackType, FeedbackReason


@dataclass
class RuleAdjustment:
    """Adjustment for a specific rule based on feedback."""
    
    rule_id: str
    original_severity: str
    adjusted_severity: Optional[str] = None
    confidence_multiplier: float = 1.0
    suppress: bool = False
    feedback_count: int = 0
    accept_rate: float = 0.0
    reject_rate: float = 0.0


@dataclass
class LearningConfig:
    """Configuration for learning model."""
    
    # Thresholds
    min_feedback_count: int = 5  # Minimum feedback before adjusting
    false_positive_threshold: float = 0.6  # Suppress if reject rate > this
    low_value_threshold: float = 0.3  # Reduce severity if accept rate < this
    high_value_threshold: float = 0.8  # Increase priority if accept rate > this
    
    # Severity adjustments
    enable_severity_adjustment: bool = True
    enable_rule_suppression: bool = True
    enable_confidence_adjustment: bool = True
    
    # Team-specific
    project_id: Optional[str] = None
    user_id: Optional[str] = None


class LearningModel:
    """Learning model that adapts based on feedback."""
    
    def __init__(
        self,
        feedback_store: FeedbackStore,
        config: Optional[LearningConfig] = None
    ):
        """
        Initialize learning model.
        
        Args:
            feedback_store: Feedback data store
            config: Learning configuration
        """
        self.feedback_store = feedback_store
        self.config = config or LearningConfig()
        self.rule_adjustments: Dict[str, RuleAdjustment] = {}
        self._load_adjustments()
    
    def _load_adjustments(self):
        """Load rule adjustments from feedback."""
        # Get all unique rule IDs
        conn = self.feedback_store._init_db.__self__.db_path
        import sqlite3
        conn = sqlite3.connect(self.feedback_store.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT rule_id FROM feedback WHERE rule_id IS NOT NULL")
        rule_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Calculate adjustments for each rule
        for rule_id in rule_ids:
            adjustment = self._calculate_adjustment(rule_id)
            if adjustment:
                self.rule_adjustments[rule_id] = adjustment
    
    def _calculate_adjustment(self, rule_id: str) -> Optional[RuleAdjustment]:
        """Calculate adjustment for a rule based on feedback."""
        feedback_list = self.feedback_store.get_feedback_for_rule(rule_id)
        
        if len(feedback_list) < self.config.min_feedback_count:
            return None
        
        # Calculate statistics
        total = len(feedback_list)
        accepts = sum(1 for fb in feedback_list if fb.feedback_type == FeedbackType.ACCEPT)
        rejects = sum(1 for fb in feedback_list if fb.feedback_type == FeedbackType.REJECT)
        
        accept_rate = accepts / total
        reject_rate = rejects / total
        
        # Get most common severity
        severities = [fb.severity for fb in feedback_list if fb.severity]
        original_severity = max(set(severities), key=severities.count) if severities else "medium"
        
        # Determine adjustments
        adjustment = RuleAdjustment(
            rule_id=rule_id,
            original_severity=original_severity,
            feedback_count=total,
            accept_rate=accept_rate,
            reject_rate=reject_rate
        )
        
        # Suppress if high false positive rate
        if self.config.enable_rule_suppression and reject_rate >= self.config.false_positive_threshold:
            adjustment.suppress = True
        
        # Adjust severity based on accept rate
        if self.config.enable_severity_adjustment:
            if accept_rate < self.config.low_value_threshold:
                adjustment.adjusted_severity = self._reduce_severity(original_severity)
            elif accept_rate > self.config.high_value_threshold:
                adjustment.adjusted_severity = self._increase_severity(original_severity)
        
        # Adjust confidence multiplier
        if self.config.enable_confidence_adjustment:
            if accept_rate > 0.8:
                adjustment.confidence_multiplier = 1.2
            elif accept_rate < 0.3:
                adjustment.confidence_multiplier = 0.7
        
        return adjustment
    
    def _reduce_severity(self, severity: str) -> str:
        """Reduce severity by one level."""
        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        try:
            idx = severity_order.index(severity.lower())
            if idx < len(severity_order) - 1:
                return severity_order[idx + 1]
        except ValueError:
            pass
        return severity
    
    def _increase_severity(self, severity: str) -> str:
        """Increase severity by one level."""
        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        try:
            idx = severity_order.index(severity.lower())
            if idx > 0:
                return severity_order[idx - 1]
        except ValueError:
            pass
        return severity
    
    def should_suppress_finding(self, rule_id: str) -> bool:
        """Check if finding should be suppressed based on feedback."""
        adjustment = self.rule_adjustments.get(rule_id)
        return adjustment.suppress if adjustment else False
    
    def get_adjusted_severity(self, rule_id: str, original_severity: str) -> str:
        """Get adjusted severity for a finding."""
        adjustment = self.rule_adjustments.get(rule_id)
        if adjustment and adjustment.adjusted_severity:
            return adjustment.adjusted_severity
        return original_severity
    
    def get_confidence_multiplier(self, rule_id: str) -> float:
        """Get confidence multiplier for a finding."""
        adjustment = self.rule_adjustments.get(rule_id)
        return adjustment.confidence_multiplier if adjustment else 1.0
    
    def apply_learning(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply learning adjustments to findings.
        
        Args:
            findings: List of finding dictionaries
            
        Returns:
            Adjusted findings list
        """
        adjusted_findings = []
        
        for finding in findings:
            rule_id = finding.get('rule_id') or finding.get('ruleId')
            
            # Skip suppressed findings
            if rule_id and self.should_suppress_finding(rule_id):
                continue
            
            # Adjust severity
            if rule_id:
                original_severity = finding.get('severity', 'medium')
                adjusted_severity = self.get_adjusted_severity(rule_id, original_severity)
                if adjusted_severity != original_severity:
                    finding['severity'] = adjusted_severity
                    finding['original_severity'] = original_severity
                    finding['severity_adjusted'] = True
                
                # Adjust confidence
                if 'confidence' in finding:
                    multiplier = self.get_confidence_multiplier(rule_id)
                    finding['confidence'] = min(100, finding['confidence'] * multiplier)
            
            adjusted_findings.append(finding)
        
        return adjusted_findings
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        total_rules = len(self.rule_adjustments)
        suppressed_rules = sum(1 for adj in self.rule_adjustments.values() if adj.suppress)
        adjusted_severities = sum(1 for adj in self.rule_adjustments.values() if adj.adjusted_severity)
        
        return {
            'total_rules_with_feedback': total_rules,
            'suppressed_rules': suppressed_rules,
            'adjusted_severities': adjusted_severities,
            'average_accept_rate': sum(adj.accept_rate for adj in self.rule_adjustments.values()) / total_rules if total_rules > 0 else 0.0,
            'average_reject_rate': sum(adj.reject_rate for adj in self.rule_adjustments.values()) / total_rules if total_rules > 0 else 0.0,
            'total_feedback': sum(adj.feedback_count for adj in self.rule_adjustments.values())
        }
    
    def export_adjustments(self, output_path: Path):
        """Export rule adjustments to JSON file."""
        data = {
            'config': {
                'min_feedback_count': self.config.min_feedback_count,
                'false_positive_threshold': self.config.false_positive_threshold,
                'low_value_threshold': self.config.low_value_threshold,
                'high_value_threshold': self.config.high_value_threshold
            },
            'stats': self.get_learning_stats(),
            'adjustments': [
                {
                    'rule_id': adj.rule_id,
                    'original_severity': adj.original_severity,
                    'adjusted_severity': adj.adjusted_severity,
                    'confidence_multiplier': adj.confidence_multiplier,
                    'suppress': adj.suppress,
                    'feedback_count': adj.feedback_count,
                    'accept_rate': adj.accept_rate,
                    'reject_rate': adj.reject_rate
                }
                for adj in self.rule_adjustments.values()
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for improving review quality."""
        recommendations = []
        
        # Find rules with high false positive rate
        for adj in self.rule_adjustments.values():
            if adj.reject_rate >= 0.5 and adj.feedback_count >= self.config.min_feedback_count:
                recommendations.append({
                    'type': 'high_false_positive',
                    'rule_id': adj.rule_id,
                    'reject_rate': adj.reject_rate,
                    'feedback_count': adj.feedback_count,
                    'recommendation': f"Consider disabling or adjusting rule '{adj.rule_id}' (reject rate: {adj.reject_rate:.1%})"
                })
        
        # Find rules with low value
        for adj in self.rule_adjustments.values():
            if adj.accept_rate < 0.3 and adj.feedback_count >= self.config.min_feedback_count:
                recommendations.append({
                    'type': 'low_value',
                    'rule_id': adj.rule_id,
                    'accept_rate': adj.accept_rate,
                    'feedback_count': adj.feedback_count,
                    'recommendation': f"Rule '{adj.rule_id}' has low acceptance rate ({adj.accept_rate:.1%}), consider reducing severity"
                })
        
        return recommendations


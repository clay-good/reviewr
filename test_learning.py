"""
Tests for learning mode and feedback system.
"""

import pytest
from pathlib import Path
import tempfile
from datetime import datetime

from reviewr.learning import (
    FeedbackType,
    FeedbackReason,
    FindingFeedback,
    FeedbackStore,
    RuleAdjustment,
    LearningConfig,
    LearningModel
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    db_path.unlink()


@pytest.fixture
def feedback_store(temp_db):
    """Create feedback store for testing."""
    return FeedbackStore(temp_db)


def test_feedback_store_init(temp_db):
    """Test feedback store initialization."""
    store = FeedbackStore(temp_db)
    assert temp_db.exists()


def test_add_and_retrieve_feedback(feedback_store):
    """Test adding and retrieving feedback."""
    feedback = FindingFeedback(
        finding_id="test-finding-1",
        feedback_type=FeedbackType.ACCEPT,
        reason=FeedbackReason.HELPFUL,
        comment="Good catch!",
        rule_id="security-sql-injection",
        severity="high",
        category="security"
    )
    
    feedback_store.add_feedback(feedback)
    
    # Retrieve feedback
    retrieved = feedback_store.get_feedback_for_finding("test-finding-1")
    assert len(retrieved) == 1
    assert retrieved[0].finding_id == "test-finding-1"
    assert retrieved[0].feedback_type == FeedbackType.ACCEPT
    assert retrieved[0].reason == FeedbackReason.HELPFUL


def test_get_feedback_for_rule(feedback_store):
    """Test retrieving feedback for a specific rule."""
    # Add multiple feedback entries for same rule
    for i in range(3):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=FeedbackType.ACCEPT if i < 2 else FeedbackType.REJECT,
            rule_id="test-rule",
            severity="medium"
        )
        feedback_store.add_feedback(feedback)
    
    # Retrieve feedback for rule
    feedback_list = feedback_store.get_feedback_for_rule("test-rule")
    assert len(feedback_list) == 3


def test_feedback_stats(feedback_store):
    """Test feedback statistics calculation."""
    # Add various feedback types
    feedback_types = [
        FeedbackType.ACCEPT,
        FeedbackType.ACCEPT,
        FeedbackType.REJECT,
        FeedbackType.SKIP
    ]
    
    for i, fb_type in enumerate(feedback_types):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=fb_type,
            rule_id="test-rule"
        )
        feedback_store.add_feedback(feedback)
    
    stats = feedback_store.get_feedback_stats("test-rule")
    
    assert stats['total'] == 4
    assert stats['accept'] == 2
    assert stats['reject'] == 1
    assert stats['skip'] == 1
    assert stats['accept_rate'] == 0.5
    assert stats['reject_rate'] == 0.25


def test_false_positive_rules(feedback_store):
    """Test identifying rules with high false positive rate."""
    # Add feedback for rule with high reject rate
    for i in range(10):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=FeedbackType.REJECT if i < 7 else FeedbackType.ACCEPT,
            rule_id="noisy-rule"
        )
        feedback_store.add_feedback(feedback)
    
    # Add feedback for rule with low reject rate
    for i in range(10):
        feedback = FindingFeedback(
            finding_id=f"finding-good-{i}",
            feedback_type=FeedbackType.ACCEPT if i < 8 else FeedbackType.REJECT,
            rule_id="good-rule"
        )
        feedback_store.add_feedback(feedback)
    
    # Get false positive rules (threshold 0.5)
    fp_rules = feedback_store.get_false_positive_rules(threshold=0.5)
    
    assert "noisy-rule" in fp_rules
    assert "good-rule" not in fp_rules


def test_learning_model_initialization(feedback_store):
    """Test learning model initialization."""
    config = LearningConfig(min_feedback_count=3)
    model = LearningModel(feedback_store, config)
    
    assert model.config.min_feedback_count == 3
    assert isinstance(model.rule_adjustments, dict)


def test_learning_model_rule_suppression(feedback_store):
    """Test rule suppression based on feedback."""
    # Add feedback with high reject rate
    for i in range(10):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=FeedbackType.REJECT if i < 7 else FeedbackType.ACCEPT,
            rule_id="suppress-me",
            severity="medium"
        )
        feedback_store.add_feedback(feedback)
    
    config = LearningConfig(
        min_feedback_count=5,
        false_positive_threshold=0.6
    )
    model = LearningModel(feedback_store, config)
    
    # Rule should be suppressed
    assert model.should_suppress_finding("suppress-me")


def test_learning_model_severity_adjustment(feedback_store):
    """Test severity adjustment based on feedback."""
    # Add feedback with low accept rate
    for i in range(10):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=FeedbackType.ACCEPT if i < 2 else FeedbackType.REJECT,
            rule_id="low-value-rule",
            severity="high"
        )
        feedback_store.add_feedback(feedback)
    
    config = LearningConfig(
        min_feedback_count=5,
        low_value_threshold=0.3
    )
    model = LearningModel(feedback_store, config)
    
    # Severity should be reduced
    adjusted = model.get_adjusted_severity("low-value-rule", "high")
    assert adjusted == "medium"


def test_learning_model_confidence_adjustment(feedback_store):
    """Test confidence multiplier adjustment."""
    # Add feedback with high accept rate
    for i in range(10):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=FeedbackType.ACCEPT if i < 9 else FeedbackType.REJECT,
            rule_id="high-value-rule",
            severity="high"
        )
        feedback_store.add_feedback(feedback)
    
    config = LearningConfig(min_feedback_count=5)
    model = LearningModel(feedback_store, config)
    
    # Confidence should be increased
    multiplier = model.get_confidence_multiplier("high-value-rule")
    assert multiplier > 1.0


def test_apply_learning_to_findings(feedback_store):
    """Test applying learning adjustments to findings."""
    # Add feedback for suppression (100% reject rate)
    for i in range(10):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=FeedbackType.REJECT,
            rule_id="suppress-rule",
            severity="medium"
        )
        feedback_store.add_feedback(feedback)

    # Add feedback for severity adjustment (20% accept rate - should reduce severity but not suppress)
    for i in range(10):
        feedback = FindingFeedback(
            finding_id=f"finding-adj-{i}",
            feedback_type=FeedbackType.ACCEPT if i < 2 else FeedbackType.SKIP,  # Changed to SKIP to avoid suppression
            rule_id="adjust-rule",
            severity="high"
        )
        feedback_store.add_feedback(feedback)

    config = LearningConfig(
        min_feedback_count=5,
        false_positive_threshold=0.6,  # Only suppress if reject rate >= 60%
        low_value_threshold=0.3
    )
    model = LearningModel(feedback_store, config)

    # Test findings
    findings = [
        {'rule_id': 'suppress-rule', 'severity': 'medium', 'message': 'Test 1'},
        {'rule_id': 'adjust-rule', 'severity': 'high', 'message': 'Test 2'},
        {'rule_id': 'unknown-rule', 'severity': 'low', 'message': 'Test 3'}
    ]

    adjusted = model.apply_learning(findings)

    # Suppressed finding should be removed
    assert len(adjusted) == 2
    assert not any(f['rule_id'] == 'suppress-rule' for f in adjusted)

    # Severity should be adjusted
    adjust_finding = next(f for f in adjusted if f['rule_id'] == 'adjust-rule')
    assert adjust_finding['severity'] == 'medium'
    assert adjust_finding['original_severity'] == 'high'


def test_learning_stats(feedback_store):
    """Test learning statistics."""
    # Add various feedback
    for i in range(5):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=FeedbackType.ACCEPT,
            rule_id="rule-1",
            severity="high"
        )
        feedback_store.add_feedback(feedback)
    
    for i in range(5):
        feedback = FindingFeedback(
            finding_id=f"finding-2-{i}",
            feedback_type=FeedbackType.REJECT,
            rule_id="rule-2",
            severity="medium"
        )
        feedback_store.add_feedback(feedback)
    
    config = LearningConfig(min_feedback_count=3)
    model = LearningModel(feedback_store, config)
    
    stats = model.get_learning_stats()
    
    assert stats['total_rules_with_feedback'] == 2
    assert stats['total_feedback'] == 10


def test_export_feedback(feedback_store, temp_db):
    """Test exporting feedback to JSON."""
    # Add some feedback
    for i in range(3):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=FeedbackType.ACCEPT,
            rule_id="test-rule"
        )
        feedback_store.add_feedback(feedback)
    
    output_path = temp_db.parent / 'feedback_export.json'
    feedback_store.export_feedback(output_path)
    
    assert output_path.exists()
    
    import json
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'feedback' in data
    assert len(data['feedback']) == 3
    
    output_path.unlink()


def test_export_adjustments(feedback_store, temp_db):
    """Test exporting adjustments to JSON."""
    # Add feedback
    for i in range(10):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=FeedbackType.ACCEPT if i < 8 else FeedbackType.REJECT,
            rule_id="test-rule",
            severity="high"
        )
        feedback_store.add_feedback(feedback)
    
    config = LearningConfig(min_feedback_count=5)
    model = LearningModel(feedback_store, config)
    
    output_path = temp_db.parent / 'adjustments_export.json'
    model.export_adjustments(output_path)
    
    assert output_path.exists()
    
    import json
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'adjustments' in data
    assert 'stats' in data
    assert 'config' in data
    
    output_path.unlink()


def test_recommendations(feedback_store):
    """Test getting recommendations."""
    # Add feedback for high false positive rule
    for i in range(10):
        feedback = FindingFeedback(
            finding_id=f"finding-{i}",
            feedback_type=FeedbackType.REJECT if i < 7 else FeedbackType.ACCEPT,
            rule_id="fp-rule",
            severity="medium"
        )
        feedback_store.add_feedback(feedback)
    
    config = LearningConfig(min_feedback_count=5)
    model = LearningModel(feedback_store, config)
    
    recommendations = model.get_recommendations()
    
    assert len(recommendations) > 0
    assert any(rec['type'] == 'high_false_positive' for rec in recommendations)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


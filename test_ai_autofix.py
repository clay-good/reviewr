"""
Tests for AI-powered autofix functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from reviewr.autofix import (
    AIFixGenerator,
    BatchFixProcessor,
    FixApplicator,
    Fix,
    FixCategory,
    FixStatus
)
from reviewr.config import ReviewrConfig, ProviderConfig
from reviewr.providers import ProviderFactory


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return ReviewrConfig(
        providers={
            'claude': ProviderConfig(
                api_key='test-key',
                model='claude-3-5-sonnet-20241022'
            )
        },
        default_provider='claude'
    )


@pytest.fixture
def provider_factory():
    """Create a provider factory."""
    return ProviderFactory()


@pytest.fixture
def sample_finding():
    """Create a sample finding."""
    return SimpleNamespace(
        file_path='test.py',
        line_start=10,
        line_end=10,
        message='Unused variable "x"',
        severity='medium',
        category='correctness',
        suggestion='Remove the unused variable'
    )


@pytest.fixture
def sample_file_content():
    """Create sample file content."""
    return """def example_function():
    x = 10
    y = 20
    return y

def another_function():
    result = 5 + 5
    return result
"""


def test_ai_generator_can_fix(mock_config, provider_factory, sample_finding):
    """Test that AI generator can determine if it can fix a finding."""
    generator = AIFixGenerator(
        language='python',
        provider_factory=provider_factory,
        config=mock_config
    )
    
    # Should be able to fix medium severity issues
    assert generator.can_fix(sample_finding)
    
    # Should not fix findings without required attributes
    invalid_finding = SimpleNamespace(message='test')
    assert not generator.can_fix(invalid_finding)


def test_ai_generator_extract_context(mock_config, provider_factory, sample_file_content):
    """Test context extraction."""
    generator = AIFixGenerator(
        language='python',
        provider_factory=provider_factory,
        config=mock_config,
        max_context_lines=10
    )
    
    context = generator._extract_context(sample_file_content, 2, 2)
    
    assert 'before' in context
    assert 'issue' in context
    assert 'after' in context
    assert context['start_line'] == 2
    assert context['end_line'] == 2
    assert 'x = 10' in context['issue']


def test_ai_generator_build_fix_prompt(mock_config, provider_factory, sample_finding, sample_file_content):
    """Test fix prompt building."""
    generator = AIFixGenerator(
        language='python',
        provider_factory=provider_factory,
        config=mock_config
    )
    
    context = generator._extract_context(sample_file_content, 2, 2)
    prompt = generator._build_fix_prompt(sample_finding, context, sample_file_content)
    
    assert 'Unused variable' in prompt
    assert 'python' in prompt.lower()
    assert 'JSON' in prompt
    assert 'fixed_code' in prompt


def test_ai_generator_determine_category(mock_config, provider_factory):
    """Test category determination."""
    generator = AIFixGenerator(
        language='python',
        provider_factory=provider_factory,
        config=mock_config
    )
    
    # Test security category
    finding = SimpleNamespace(category='security-vulnerability')
    assert generator._determine_category(finding) == FixCategory.SECURITY
    
    # Test performance category
    finding = SimpleNamespace(category='performance-issue')
    assert generator._determine_category(finding) == FixCategory.PERFORMANCE
    
    # Test default category
    finding = SimpleNamespace(category='unknown')
    assert generator._determine_category(finding) == FixCategory.CORRECTNESS


def test_batch_processor_filter_fixes():
    """Test fix filtering."""
    applicator = FixApplicator(dry_run=True)
    processor = BatchFixProcessor(applicator=applicator)
    
    fixes = [
        Fix(
            fix_id='1',
            category=FixCategory.SECURITY,
            file_path='test.py',
            line_start=1,
            line_end=1,
            description='Fix 1',
            old_code='old',
            new_code='new',
            confidence=0.9,
            safe=True
        ),
        Fix(
            fix_id='2',
            category=FixCategory.STYLE,
            file_path='test.py',
            line_start=2,
            line_end=2,
            description='Fix 2',
            old_code='old',
            new_code='new',
            confidence=0.5,
            safe=False
        ),
        Fix(
            fix_id='3',
            category=FixCategory.PERFORMANCE,
            file_path='test.py',
            line_start=3,
            line_end=3,
            description='Fix 3',
            old_code='old',
            new_code='new',
            confidence=0.8,
            safe=True
        ),
    ]
    
    # Test safe_only filter
    filtered = processor._filter_fixes(fixes, safe_only=True, min_confidence=0.0, categories=None)
    assert len(filtered) == 2
    assert all(f.safe for f in filtered)
    
    # Test confidence filter
    filtered = processor._filter_fixes(fixes, safe_only=False, min_confidence=0.8, categories=None)
    assert len(filtered) == 2
    assert all(f.confidence >= 0.8 for f in filtered)
    
    # Test category filter
    filtered = processor._filter_fixes(fixes, safe_only=False, min_confidence=0.0, categories=['security'])
    assert len(filtered) == 1
    assert filtered[0].category == FixCategory.SECURITY


def test_batch_processor_group_fixes_by_file():
    """Test grouping fixes by file."""
    applicator = FixApplicator(dry_run=True)
    processor = BatchFixProcessor(applicator=applicator)
    
    fixes = [
        Fix(
            fix_id='1',
            category=FixCategory.SECURITY,
            file_path='test1.py',
            line_start=1,
            line_end=1,
            description='Fix 1',
            old_code='old',
            new_code='new'
        ),
        Fix(
            fix_id='2',
            category=FixCategory.STYLE,
            file_path='test2.py',
            line_start=1,
            line_end=1,
            description='Fix 2',
            old_code='old',
            new_code='new'
        ),
        Fix(
            fix_id='3',
            category=FixCategory.PERFORMANCE,
            file_path='test1.py',
            line_start=2,
            line_end=2,
            description='Fix 3',
            old_code='old',
            new_code='new'
        ),
    ]
    
    grouped = processor._group_fixes_by_file(fixes)
    
    assert len(grouped) == 2
    assert 'test1.py' in grouped
    assert 'test2.py' in grouped
    assert len(grouped['test1.py']) == 2
    assert len(grouped['test2.py']) == 1


def test_batch_processor_ranges_overlap():
    """Test range overlap detection."""
    applicator = FixApplicator(dry_run=True)
    processor = BatchFixProcessor(applicator=applicator)
    
    # Overlapping ranges
    assert processor._ranges_overlap(1, 5, 3, 7)
    assert processor._ranges_overlap(3, 7, 1, 5)
    assert processor._ranges_overlap(1, 10, 5, 6)
    
    # Non-overlapping ranges
    assert not processor._ranges_overlap(1, 5, 6, 10)
    assert not processor._ranges_overlap(6, 10, 1, 5)


def test_batch_processor_resolve_conflicts():
    """Test conflict resolution."""
    applicator = FixApplicator(dry_run=True)
    processor = BatchFixProcessor(applicator=applicator)
    
    # Create conflicting fixes (overlapping line ranges)
    fixes_by_file = {
        'test.py': [
            Fix(
                fix_id='1',
                category=FixCategory.SECURITY,
                file_path='test.py',
                line_start=1,
                line_end=5,
                description='Fix 1',
                old_code='old',
                new_code='new',
                confidence=0.9
            ),
            Fix(
                fix_id='2',
                category=FixCategory.STYLE,
                file_path='test.py',
                line_start=3,
                line_end=7,
                description='Fix 2',
                old_code='old',
                new_code='new',
                confidence=0.7
            ),
            Fix(
                fix_id='3',
                category=FixCategory.PERFORMANCE,
                file_path='test.py',
                line_start=10,
                line_end=15,
                description='Fix 3',
                old_code='old',
                new_code='new',
                confidence=0.8
            ),
        ]
    }
    
    resolved = processor._resolve_conflicts(fixes_by_file)
    
    # Should resolve to 2 fixes (highest confidence from conflict + non-conflicting)
    assert len(resolved) == 2
    
    # First fix should be the one with highest confidence (0.9)
    assert resolved[0].fix_id == '1'
    
    # Second fix should be the non-conflicting one
    assert resolved[1].fix_id == '3'


def test_batch_processor_process_fixes(tmp_path):
    """Test batch fix processing."""
    # Create a test file
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 10\ny = 20\nprint(x + y)\n")
    
    # Create fixes
    fixes = [
        Fix(
            fix_id='1',
            category=FixCategory.STYLE,
            file_path=str(test_file),
            line_start=1,
            line_end=1,
            description='Fix variable name',
            old_code='x = 10',
            new_code='value_x = 10',
            confidence=0.9,
            safe=True
        ),
    ]
    
    # Create applicator and processor
    applicator = FixApplicator(
        backup_dir=str(tmp_path / "backups"),
        dry_run=True,
        validate_syntax=False
    )
    processor = BatchFixProcessor(applicator=applicator)
    
    # Process fixes
    result = processor.process_fixes(fixes, safe_only=False, min_confidence=0.0)
    
    assert result.total_fixes == 1
    assert result.successful == 1
    assert result.failed == 0
    assert result.skipped == 0
    assert result.success_rate == 1.0


def test_fix_to_dict():
    """Test Fix serialization."""
    fix = Fix(
        fix_id='test-123',
        category=FixCategory.SECURITY,
        file_path='test.py',
        line_start=10,
        line_end=15,
        description='Test fix',
        old_code='old code',
        new_code='new code',
        confidence=0.95,
        safe=True,
        requires_validation=True,
        finding_message='Test finding',
        explanation='Test explanation'
    )
    
    fix_dict = fix.to_dict()
    
    assert fix_dict['fix_id'] == 'test-123'
    assert fix_dict['category'] == 'security'
    assert fix_dict['file_path'] == 'test.py'
    assert fix_dict['confidence'] == 0.95
    assert fix_dict['safe'] is True


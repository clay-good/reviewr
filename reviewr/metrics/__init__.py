"""
Code metrics module for reviewr.

Provides comprehensive code quality metrics including:
- Cyclomatic complexity
- Cognitive complexity
- Maintainability index
- Halstead metrics
- Code duplication detection
- Technical debt estimation
"""

from .complexity import (
    ComplexityAnalyzer,
    ComplexityMetrics,
    CyclomaticComplexity,
    CognitiveComplexity,
    HalsteadMetrics,
    MaintainabilityIndex
)

from .duplication import (
    DuplicationDetector,
    DuplicateBlock,
    DuplicationReport
)

from .debt import (
    TechnicalDebtEstimator,
    DebtItem,
    DebtReport,
    DebtSeverity
)

__all__ = [
    # Complexity
    'ComplexityAnalyzer',
    'ComplexityMetrics',
    'CyclomaticComplexity',
    'CognitiveComplexity',
    'HalsteadMetrics',
    'MaintainabilityIndex',
    
    # Duplication
    'DuplicationDetector',
    'DuplicateBlock',
    'DuplicationReport',
    
    # Technical Debt
    'TechnicalDebtEstimator',
    'DebtItem',
    'DebtReport',
    'DebtSeverity',
]


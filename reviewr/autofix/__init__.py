"""Auto-fix capabilities for reviewr."""

from .base import (
    FixGenerator,
    Fix,
    FixResult,
    FixStatus,
    FixCategory,
    CompositeFixGenerator
)
from .applicator import FixApplicator
from .python_fixes import PythonFixGenerator
from .javascript_fixes import JavaScriptFixGenerator
from .ai_generator import AIFixGenerator
from .batch_processor import BatchFixProcessor, BatchResult

__all__ = [
    'FixGenerator',
    'Fix',
    'FixResult',
    'FixStatus',
    'FixCategory',
    'CompositeFixGenerator',
    'FixApplicator',
    'PythonFixGenerator',
    'JavaScriptFixGenerator',
    'AIFixGenerator',
    'BatchFixProcessor',
    'BatchResult',
]


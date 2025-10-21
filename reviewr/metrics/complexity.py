"""
Code complexity metrics analyzer.

Provides:
- Cyclomatic complexity (McCabe)
- Cognitive complexity (SonarSource)
- Halstead metrics
- Maintainability index
"""

import ast
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from enum import Enum


class ComplexityLevel(Enum):
    """Complexity level classification."""
    LOW = "low"           # 1-5
    MODERATE = "moderate" # 6-10
    HIGH = "high"         # 11-20
    VERY_HIGH = "very_high" # 21-50
    EXTREME = "extreme"   # 50+


@dataclass
class ComplexityMetrics:
    """Comprehensive complexity metrics for a function or method."""
    name: str
    line_start: int
    line_end: int
    cyclomatic: int
    cognitive: int
    halstead_volume: float
    halstead_difficulty: float
    halstead_effort: float
    maintainability_index: float
    lines_of_code: int
    parameters: int
    nesting_depth: int
    
    @property
    def cyclomatic_level(self) -> ComplexityLevel:
        """Get cyclomatic complexity level."""
        if self.cyclomatic <= 5:
            return ComplexityLevel.LOW
        elif self.cyclomatic <= 10:
            return ComplexityLevel.MODERATE
        elif self.cyclomatic <= 20:
            return ComplexityLevel.HIGH
        elif self.cyclomatic <= 50:
            return ComplexityLevel.VERY_HIGH
        else:
            return ComplexityLevel.EXTREME
    
    @property
    def cognitive_level(self) -> ComplexityLevel:
        """Get cognitive complexity level."""
        if self.cognitive <= 5:
            return ComplexityLevel.LOW
        elif self.cognitive <= 10:
            return ComplexityLevel.MODERATE
        elif self.cognitive <= 15:
            return ComplexityLevel.HIGH
        elif self.cognitive <= 25:
            return ComplexityLevel.VERY_HIGH
        else:
            return ComplexityLevel.EXTREME
    
    @property
    def is_complex(self) -> bool:
        """Check if function is too complex."""
        return self.cyclomatic > 10 or self.cognitive > 15
    
    @property
    def is_maintainable(self) -> bool:
        """Check if function is maintainable."""
        return self.maintainability_index >= 65


@dataclass
class HalsteadMetrics:
    """Halstead complexity metrics."""
    n1: int  # Number of distinct operators
    n2: int  # Number of distinct operands
    N1: int  # Total number of operators
    N2: int  # Total number of operands
    
    @property
    def vocabulary(self) -> int:
        """Program vocabulary (n = n1 + n2)."""
        return self.n1 + self.n2
    
    @property
    def length(self) -> int:
        """Program length (N = N1 + N2)."""
        return self.N1 + self.N2
    
    @property
    def volume(self) -> float:
        """Program volume (V = N * log2(n))."""
        if self.vocabulary == 0:
            return 0.0
        return self.length * math.log2(self.vocabulary)
    
    @property
    def difficulty(self) -> float:
        """Program difficulty (D = (n1/2) * (N2/n2))."""
        if self.n2 == 0:
            return 0.0
        return (self.n1 / 2) * (self.N2 / self.n2)
    
    @property
    def effort(self) -> float:
        """Program effort (E = D * V)."""
        return self.difficulty * self.volume


class CyclomaticComplexity(ast.NodeVisitor):
    """Calculate cyclomatic complexity (McCabe)."""
    
    def __init__(self):
        self.complexity = 1  # Start at 1
        
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        # Each additional boolean operator adds complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_comprehension(self, node):
        self.complexity += 1
        self.generic_visit(node)


class CognitiveComplexity(ast.NodeVisitor):
    """Calculate cognitive complexity (SonarSource)."""
    
    def __init__(self):
        self.complexity = 0
        self.nesting_level = 0
        self.nesting_increments = {
            ast.If, ast.While, ast.For, ast.ExceptHandler,
            ast.With, ast.Lambda
        }
    
    def _increment_nesting(self, node):
        """Increment nesting level for certain nodes."""
        if type(node) in self.nesting_increments:
            self.nesting_level += 1
            self.generic_visit(node)
            self.nesting_level -= 1
        else:
            self.generic_visit(node)
    
    def visit_If(self, node):
        self.complexity += 1 + self.nesting_level
        self._increment_nesting(node)
    
    def visit_While(self, node):
        self.complexity += 1 + self.nesting_level
        self._increment_nesting(node)
    
    def visit_For(self, node):
        self.complexity += 1 + self.nesting_level
        self._increment_nesting(node)
    
    def visit_ExceptHandler(self, node):
        self.complexity += 1 + self.nesting_level
        self._increment_nesting(node)
    
    def visit_BoolOp(self, node):
        # Each additional boolean operator adds complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_Lambda(self, node):
        self.complexity += 1
        self._increment_nesting(node)
    
    def visit_Continue(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Break(self, node):
        self.complexity += 1
        self.generic_visit(node)


class HalsteadAnalyzer(ast.NodeVisitor):
    """Calculate Halstead metrics."""
    
    OPERATORS = {
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
        ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd,
        ast.FloorDiv, ast.And, ast.Or, ast.Eq, ast.NotEq, ast.Lt,
        ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn,
        ast.Not, ast.Invert, ast.UAdd, ast.USub
    }
    
    def __init__(self):
        self.operators: List[str] = []
        self.operands: List[str] = []
    
    def visit_BinOp(self, node):
        self.operators.append(type(node.op).__name__)
        self.generic_visit(node)
    
    def visit_UnaryOp(self, node):
        self.operators.append(type(node.op).__name__)
        self.generic_visit(node)
    
    def visit_Compare(self, node):
        for op in node.ops:
            self.operators.append(type(op).__name__)
        self.generic_visit(node)
    
    def visit_BoolOp(self, node):
        self.operators.append(type(node.op).__name__)
        self.generic_visit(node)
    
    def visit_Name(self, node):
        self.operands.append(node.id)
        self.generic_visit(node)
    
    def visit_Constant(self, node):
        self.operands.append(str(node.value))
        self.generic_visit(node)
    
    def visit_Attribute(self, node):
        self.operands.append(node.attr)
        self.generic_visit(node)
    
    def get_metrics(self) -> HalsteadMetrics:
        """Get Halstead metrics."""
        n1 = len(set(self.operators))
        n2 = len(set(self.operands))
        N1 = len(self.operators)
        N2 = len(self.operands)
        
        return HalsteadMetrics(n1=n1, n2=n2, N1=N1, N2=N2)


class MaintainabilityIndex:
    """Calculate maintainability index."""
    
    @staticmethod
    def calculate(
        halstead_volume: float,
        cyclomatic: int,
        lines_of_code: int
    ) -> float:
        """
        Calculate maintainability index.
        
        MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(LOC)
        
        Where:
        - V = Halstead Volume
        - G = Cyclomatic Complexity
        - LOC = Lines of Code
        
        Normalized to 0-100 scale.
        """
        if lines_of_code == 0 or halstead_volume == 0:
            return 100.0
        
        mi = (
            171
            - 5.2 * math.log(halstead_volume)
            - 0.23 * cyclomatic
            - 16.2 * math.log(lines_of_code)
        )
        
        # Normalize to 0-100
        mi = max(0, (mi / 171) * 100)
        
        return round(mi, 2)


class ComplexityAnalyzer:
    """Analyze code complexity metrics."""
    
    def __init__(self):
        self.metrics: List[ComplexityMetrics] = []
    
    def analyze_file(self, file_path: Path) -> List[ComplexityMetrics]:
        """Analyze a Python file."""
        try:
            code = file_path.read_text()
            tree = ast.parse(code)
            
            self.metrics = []
            self._analyze_tree(tree)
            
            return self.metrics
        
        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")
            return []
    
    def _analyze_tree(self, tree: ast.AST):
        """Analyze AST tree."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics = self._analyze_function(node)
                if metrics:
                    self.metrics.append(metrics)
    
    def _analyze_function(
        self,
        node: ast.FunctionDef
    ) -> Optional[ComplexityMetrics]:
        """Analyze a function."""
        try:
            # Cyclomatic complexity
            cyclomatic_visitor = CyclomaticComplexity()
            cyclomatic_visitor.visit(node)
            cyclomatic = cyclomatic_visitor.complexity
            
            # Cognitive complexity
            cognitive_visitor = CognitiveComplexity()
            cognitive_visitor.visit(node)
            cognitive = cognitive_visitor.complexity
            
            # Halstead metrics
            halstead_visitor = HalsteadAnalyzer()
            halstead_visitor.visit(node)
            halstead = halstead_visitor.get_metrics()
            
            # Lines of code
            lines_of_code = node.end_lineno - node.lineno + 1
            
            # Parameters
            parameters = len(node.args.args)
            
            # Nesting depth
            nesting_depth = self._calculate_nesting_depth(node)
            
            # Maintainability index
            mi = MaintainabilityIndex.calculate(
                halstead.volume,
                cyclomatic,
                lines_of_code
            )
            
            return ComplexityMetrics(
                name=node.name,
                line_start=node.lineno,
                line_end=node.end_lineno,
                cyclomatic=cyclomatic,
                cognitive=cognitive,
                halstead_volume=halstead.volume,
                halstead_difficulty=halstead.difficulty,
                halstead_effort=halstead.effort,
                maintainability_index=mi,
                lines_of_code=lines_of_code,
                parameters=parameters,
                nesting_depth=nesting_depth
            )
        
        except Exception as e:
            print(f"Warning: Failed to analyze function {node.name}: {e}")
            return None
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        
        class DepthVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_depth = 0
                self.max_depth = 0
            
            def visit_If(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
            
            def visit_While(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
            
            def visit_For(self, node):
                self.current_depth += 1
                self.max_depth = max(self.max_depth, self.current_depth)
                self.generic_visit(node)
                self.current_depth -= 1
        
        visitor = DepthVisitor()
        visitor.visit(node)
        
        return visitor.max_depth
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.metrics:
            return {}
        
        return {
            "total_functions": len(self.metrics),
            "avg_cyclomatic": sum(m.cyclomatic for m in self.metrics) / len(self.metrics),
            "avg_cognitive": sum(m.cognitive for m in self.metrics) / len(self.metrics),
            "avg_maintainability": sum(m.maintainability_index for m in self.metrics) / len(self.metrics),
            "complex_functions": len([m for m in self.metrics if m.is_complex]),
            "unmaintainable_functions": len([m for m in self.metrics if not m.is_maintainable]),
            "max_cyclomatic": max(m.cyclomatic for m in self.metrics),
            "max_cognitive": max(m.cognitive for m in self.metrics),
            "max_nesting": max(m.nesting_depth for m in self.metrics)
        }


"""
Advanced complexity metrics analyzer for Python code.

This module provides sophisticated complexity analysis including:
- Cyclomatic complexity (McCabe)
- Cognitive complexity
- Halstead metrics
- Maintainability index
- Code churn estimation
- Technical debt calculation
"""

import ast
import math
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter

from .base import LocalAnalyzer, LocalFinding, FindingSeverity


@dataclass
class ComplexityMetrics:
    """Container for all complexity metrics of a function."""
    name: str
    line_start: int
    line_end: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    halstead_difficulty: float
    halstead_effort: float
    halstead_volume: float
    maintainability_index: float
    lines_of_code: int
    comment_ratio: float


class ComplexityAnalyzer(LocalAnalyzer):
    """Advanced complexity analyzer with multiple metrics."""
    
    def __init__(self):
        """Initialize the complexity analyzer."""
        self.cyclomatic_threshold = 10
        self.cognitive_threshold = 15
        self.maintainability_threshold = 65  # Below this is concerning
        self.halstead_difficulty_threshold = 30
    
    def supports_language(self, language: str) -> bool:
        """Check if this analyzer supports Python."""
        return language.lower() == 'python'
    
    def analyze(self, file_path: str, content: str) -> List[LocalFinding]:
        """
        Perform comprehensive complexity analysis.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            List of complexity findings
        """
        findings = []
        
        try:
            tree = ast.parse(content, filename=file_path)
        except (SyntaxError, Exception):
            return findings
        
        # Analyze each function
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics = self._calculate_all_metrics(node, content)
                findings.extend(self._generate_findings(metrics, file_path))
        
        # Analyze module-level complexity
        module_findings = self._analyze_module_complexity(tree, file_path, content)
        findings.extend(module_findings)
        
        return findings
    
    def _calculate_all_metrics(self, func_node: ast.FunctionDef, content: str) -> ComplexityMetrics:
        """Calculate all complexity metrics for a function."""
        # Cyclomatic complexity
        cyclomatic = self._calculate_cyclomatic_complexity(func_node)
        
        # Cognitive complexity
        cognitive = self._calculate_cognitive_complexity(func_node)
        
        # Halstead metrics
        halstead = self._calculate_halstead_metrics(func_node)
        
        # Lines of code
        loc = func_node.end_lineno - func_node.lineno + 1 if func_node.end_lineno else 1
        
        # Comment ratio
        comment_ratio = self._calculate_comment_ratio(func_node, content)
        
        # Maintainability index
        maintainability = self._calculate_maintainability_index(
            halstead['volume'], cyclomatic, loc, comment_ratio
        )
        
        return ComplexityMetrics(
            name=func_node.name,
            line_start=func_node.lineno,
            line_end=func_node.end_lineno or func_node.lineno,
            cyclomatic_complexity=cyclomatic,
            cognitive_complexity=cognitive,
            halstead_difficulty=halstead['difficulty'],
            halstead_effort=halstead['effort'],
            halstead_volume=halstead['volume'],
            maintainability_index=maintainability,
            lines_of_code=loc,
            comment_ratio=comment_ratio
        )
    
    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """
        Calculate McCabe cyclomatic complexity.
        
        Cyclomatic complexity = E - N + 2P
        where E = edges, N = nodes, P = connected components
        
        Simplified: count decision points + 1
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Each boolean operator adds a path
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
                complexity += len(child.ifs)
            # Pattern matching (Python 3.10+)
            elif hasattr(ast, 'Match') and isinstance(child, ast.Match):
                complexity += len(child.cases)
        
        return complexity
    
    def _calculate_cognitive_complexity(self, node: ast.AST, nesting_level: int = 0) -> int:
        """
        Calculate cognitive complexity.
        
        Cognitive complexity measures how difficult code is to understand.
        It penalizes nesting more heavily than cyclomatic complexity.
        """
        complexity = 0
        
        for child in ast.iter_child_nodes(node):
            # Control flow structures
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                # Add 1 for the structure + nesting level
                complexity += 1 + nesting_level
                # Recursively calculate for nested code
                complexity += self._calculate_cognitive_complexity(child, nesting_level + 1)
            
            elif isinstance(child, ast.Try):
                complexity += 1 + nesting_level
                complexity += self._calculate_cognitive_complexity(child, nesting_level + 1)
            
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1 + nesting_level
                complexity += self._calculate_cognitive_complexity(child, nesting_level + 1)
            
            # Boolean operators in conditions
            elif isinstance(child, ast.BoolOp):
                # Each additional boolean operator adds complexity
                complexity += len(child.values) - 1
            
            # Recursion
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    # Check if calling itself (recursion)
                    if hasattr(node, 'name') and child.func.id == node.name:
                        complexity += 1
            
            # Continue recursion for other nodes
            else:
                complexity += self._calculate_cognitive_complexity(child, nesting_level)
        
        return complexity
    
    def _calculate_halstead_metrics(self, node: ast.AST) -> Dict[str, float]:
        """
        Calculate Halstead complexity metrics.
        
        Halstead metrics measure program vocabulary and length:
        - n1 = number of distinct operators
        - n2 = number of distinct operands
        - N1 = total number of operators
        - N2 = total number of operands
        
        Derived metrics:
        - Program vocabulary: n = n1 + n2
        - Program length: N = N1 + N2
        - Volume: V = N * log2(n)
        - Difficulty: D = (n1/2) * (N2/n2)
        - Effort: E = D * V
        """
        operators = []
        operands = []
        
        for child in ast.walk(node):
            # Operators
            if isinstance(child, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod,
                                 ast.Pow, ast.FloorDiv, ast.BitAnd, ast.BitOr,
                                 ast.BitXor, ast.LShift, ast.RShift)):
                operators.append(type(child).__name__)
            
            elif isinstance(child, (ast.And, ast.Or, ast.Not)):
                operators.append(type(child).__name__)
            
            elif isinstance(child, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt,
                                   ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn)):
                operators.append(type(child).__name__)
            
            elif isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                operators.append(type(child).__name__)
            
            elif isinstance(child, ast.Call):
                operators.append('Call')
            
            # Operands
            elif isinstance(child, ast.Name):
                operands.append(child.id)
            
            elif isinstance(child, ast.Constant):
                operands.append(str(child.value))
        
        # Calculate metrics
        n1 = len(set(operators))  # Distinct operators
        n2 = len(set(operands))   # Distinct operands
        N1 = len(operators)        # Total operators
        N2 = len(operands)         # Total operands
        
        # Avoid division by zero
        if n1 == 0 or n2 == 0 or N2 == 0:
            return {
                'vocabulary': 0,
                'length': 0,
                'volume': 0,
                'difficulty': 0,
                'effort': 0
            }
        
        n = n1 + n2  # Program vocabulary
        N = N1 + N2  # Program length
        
        V = N * math.log2(n) if n > 0 else 0  # Volume
        D = (n1 / 2) * (N2 / n2)               # Difficulty
        E = D * V                               # Effort
        
        return {
            'vocabulary': n,
            'length': N,
            'volume': V,
            'difficulty': D,
            'effort': E
        }
    
    def _calculate_maintainability_index(
        self,
        halstead_volume: float,
        cyclomatic_complexity: int,
        lines_of_code: int,
        comment_ratio: float
    ) -> float:
        """
        Calculate maintainability index.
        
        MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(LOC) + 50 * sin(sqrt(2.4 * C))
        
        where:
        - V = Halstead Volume
        - G = Cyclomatic Complexity
        - LOC = Lines of Code
        - C = Comment ratio (0-1)
        
        Result is normalized to 0-100 scale:
        - 85-100: Highly maintainable
        - 65-85: Moderately maintainable
        - <65: Difficult to maintain
        """
        if lines_of_code == 0 or halstead_volume == 0:
            return 100.0
        
        try:
            mi = (171 - 
                  5.2 * math.log(halstead_volume) - 
                  0.23 * cyclomatic_complexity - 
                  16.2 * math.log(lines_of_code) +
                  50 * math.sin(math.sqrt(2.4 * comment_ratio)))
            
            # Normalize to 0-100
            mi = max(0, min(100, mi))
            return mi
        except (ValueError, ZeroDivisionError):
            return 100.0
    
    def _calculate_comment_ratio(self, node: ast.AST, content: str) -> float:
        """Calculate the ratio of comments to code."""
        if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
            return 0.0
        
        lines = content.split('\n')[node.lineno-1:node.end_lineno]
        
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        total_lines = len(lines)
        
        return comment_lines / total_lines if total_lines > 0 else 0.0

    def _generate_findings(self, metrics: ComplexityMetrics, file_path: str) -> List[LocalFinding]:
        """Generate findings based on complexity metrics."""
        findings = []

        # Cyclomatic complexity
        if metrics.cyclomatic_complexity > self.cyclomatic_threshold:
            severity = FindingSeverity.LOW.value
            if metrics.cyclomatic_complexity > 20:
                severity = FindingSeverity.HIGH.value
            elif metrics.cyclomatic_complexity > 15:
                severity = FindingSeverity.MEDIUM.value

            findings.append(LocalFinding(
                file_path=file_path,
                line_start=metrics.line_start,
                line_end=metrics.line_end,
                severity=severity,
                category='complexity',
                message=f"Function '{metrics.name}' has high cyclomatic complexity ({metrics.cyclomatic_complexity})",
                suggestion=f"Consider breaking this function into smaller functions. Target: <{self.cyclomatic_threshold}",
                metric_value=float(metrics.cyclomatic_complexity),
                metric_name='cyclomatic_complexity'
            ))

        # Cognitive complexity
        if metrics.cognitive_complexity > self.cognitive_threshold:
            severity = FindingSeverity.MEDIUM.value
            if metrics.cognitive_complexity > 30:
                severity = FindingSeverity.HIGH.value

            findings.append(LocalFinding(
                file_path=file_path,
                line_start=metrics.line_start,
                line_end=metrics.line_end,
                severity=severity,
                category='complexity',
                message=f"Function '{metrics.name}' has high cognitive complexity ({metrics.cognitive_complexity})",
                suggestion=f"Reduce nesting and simplify control flow. Target: <{self.cognitive_threshold}",
                metric_value=float(metrics.cognitive_complexity),
                metric_name='cognitive_complexity'
            ))

        # Halstead difficulty
        if metrics.halstead_difficulty > self.halstead_difficulty_threshold:
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=metrics.line_start,
                line_end=metrics.line_end,
                severity=FindingSeverity.MEDIUM.value,
                category='complexity',
                message=f"Function '{metrics.name}' has high Halstead difficulty ({metrics.halstead_difficulty:.1f})",
                suggestion="Simplify the code by reducing the number of operators and operands",
                metric_value=metrics.halstead_difficulty,
                metric_name='halstead_difficulty'
            ))

        # Maintainability index
        if metrics.maintainability_index < self.maintainability_threshold:
            severity = FindingSeverity.MEDIUM.value
            if metrics.maintainability_index < 40:
                severity = FindingSeverity.HIGH.value

            findings.append(LocalFinding(
                file_path=file_path,
                line_start=metrics.line_start,
                line_end=metrics.line_end,
                severity=severity,
                category='maintainability',
                message=f"Function '{metrics.name}' has low maintainability index ({metrics.maintainability_index:.1f})",
                suggestion="Improve maintainability by: reducing complexity, adding comments, and breaking into smaller functions",
                metric_value=metrics.maintainability_index,
                metric_name='maintainability_index'
            ))

        # Technical debt estimation
        if metrics.cyclomatic_complexity > 15 or metrics.cognitive_complexity > 20:
            # Estimate time to refactor (rough heuristic)
            debt_hours = (metrics.cyclomatic_complexity * 0.5 +
                         metrics.cognitive_complexity * 0.3)

            findings.append(LocalFinding(
                file_path=file_path,
                line_start=metrics.line_start,
                line_end=metrics.line_end,
                severity=FindingSeverity.INFO.value,
                category='technical_debt',
                message=f"Function '{metrics.name}' has estimated technical debt of {debt_hours:.1f} hours",
                suggestion=f"Refactoring this function would improve code quality. Estimated effort: {debt_hours:.1f} hours",
                metric_value=debt_hours,
                metric_name='technical_debt_hours'
            ))

        return findings

    def _analyze_module_complexity(self, tree: ast.AST, file_path: str, content: str) -> List[LocalFinding]:
        """Analyze module-level complexity."""
        findings = []

        # Count classes and functions
        num_classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        num_functions = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))

        # Calculate average complexity
        complexities = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = self._calculate_cyclomatic_complexity(node)
                complexities.append(complexity)

        if complexities:
            avg_complexity = sum(complexities) / len(complexities)
            max_complexity = max(complexities)

            # Warn if average complexity is high
            if avg_complexity > 8:
                findings.append(LocalFinding(
                    file_path=file_path,
                    line_start=1,
                    line_end=1,
                    severity=FindingSeverity.MEDIUM.value,
                    category='complexity',
                    message=f"Module has high average complexity ({avg_complexity:.1f})",
                    suggestion="Consider refactoring complex functions to improve overall code quality",
                    metric_value=avg_complexity,
                    metric_name='average_complexity'
                ))

        # Warn if module is too large
        lines = content.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])

        if loc > 500:
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=1,
                line_end=1,
                severity=FindingSeverity.LOW.value,
                category='maintainability',
                message=f"Module is very large ({loc} lines of code)",
                suggestion="Consider splitting this module into smaller, more focused modules",
                metric_value=float(loc),
                metric_name='lines_of_code'
            ))

        # Warn if too many classes/functions
        if num_classes > 10:
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=1,
                line_end=1,
                severity=FindingSeverity.LOW.value,
                category='maintainability',
                message=f"Module has many classes ({num_classes})",
                suggestion="Consider organizing classes into separate modules",
                metric_value=float(num_classes),
                metric_name='class_count'
            ))

        if num_functions > 20:
            findings.append(LocalFinding(
                file_path=file_path,
                line_start=1,
                line_end=1,
                severity=FindingSeverity.LOW.value,
                category='maintainability',
                message=f"Module has many functions ({num_functions})",
                suggestion="Consider organizing functions into classes or separate modules",
                metric_value=float(num_functions),
                metric_name='function_count'
            ))

        return findings

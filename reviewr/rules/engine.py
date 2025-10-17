import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Pattern
from enum import Enum


class RuleSeverity(Enum):
    """Severity levels for custom rules."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RuleMatch:
    """A match found by a custom rule."""
    
    rule_id: str
    file_path: str
    line_number: int
    column: int
    matched_text: str
    severity: str
    message: str
    suggestion: Optional[str] = None
    
    def to_local_finding(self):
        """Convert to LocalFinding format."""
        from ..analysis.base import LocalFinding
        
        return LocalFinding(
            file_path=self.file_path,
            line_start=self.line_number,
            line_end=self.line_number,
            severity=self.severity,
            category='custom_rule',
            message=f"[{self.rule_id}] {self.message}",
            suggestion=self.suggestion,
            code_snippet=self.matched_text
        )


@dataclass
class Rule:
    """A custom rule definition."""
    
    id: str
    name: str
    description: str
    pattern: str
    severity: str
    message: str
    suggestion: Optional[str] = None
    languages: Optional[List[str]] = None
    enabled: bool = True
    case_sensitive: bool = True
    multiline: bool = False
    
    _compiled_pattern: Optional[Pattern] = None
    
    def compile(self) -> Pattern:
        """Compile the regex pattern."""
        if self._compiled_pattern is None:
            flags = 0
            if not self.case_sensitive:
                flags |= re.IGNORECASE
            if self.multiline:
                flags |= re.MULTILINE | re.DOTALL
            
            self._compiled_pattern = re.compile(self.pattern, flags)
        
        return self._compiled_pattern
    
    def matches_language(self, language: str) -> bool:
        """Check if this rule applies to the given language."""
        if self.languages is None:
            return True  # Apply to all languages
        return language.lower() in [lang.lower() for lang in self.languages]


class RulesEngine:
    """Engine for applying custom rules to code."""
    
    def __init__(self, rules: Optional[List[Rule]] = None):
        """
        Initialize the rules engine.
        
        Args:
            rules: List of custom rules to apply
        """
        self.rules = rules or []
        self._compile_rules()
    
    def _compile_rules(self):
        """Compile all rule patterns."""
        for rule in self.rules:
            if rule.enabled:
                rule.compile()
    
    def add_rule(self, rule: Rule):
        """Add a new rule to the engine."""
        rule.compile()
        self.rules.append(rule)
    
    def remove_rule(self, rule_id: str):
        """Remove a rule by ID."""
        self.rules = [r for r in self.rules if r.id != rule_id]
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a rule by ID."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None
    
    def enable_rule(self, rule_id: str):
        """Enable a rule by ID."""
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = True
    
    def disable_rule(self, rule_id: str):
        """Disable a rule by ID."""
        rule = self.get_rule(rule_id)
        if rule:
            rule.enabled = False
    
    def analyze(self, file_path: str, content: str, language: str) -> List[RuleMatch]:
        """
        Analyze code against all applicable rules.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            
        Returns:
            List of rule matches
        """
        matches = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if not rule.matches_language(language):
                continue
            
            rule_matches = self._apply_rule(rule, file_path, content)
            matches.extend(rule_matches)
        
        return matches
    
    def _apply_rule(self, rule: Rule, file_path: str, content: str) -> List[RuleMatch]:
        """Apply a single rule to content."""
        matches = []
        pattern = rule.compile()
        
        for match in pattern.finditer(content):
            # Calculate line number and column
            line_number = content[:match.start()].count('\n') + 1
            line_start = content.rfind('\n', 0, match.start()) + 1
            column = match.start() - line_start + 1
            
            matches.append(RuleMatch(
                rule_id=rule.id,
                file_path=file_path,
                line_number=line_number,
                column=column,
                matched_text=match.group(0),
                severity=rule.severity,
                message=rule.message,
                suggestion=rule.suggestion
            ))
        
        return matches
    
    def get_enabled_rules(self) -> List[Rule]:
        """Get all enabled rules."""
        return [r for r in self.rules if r.enabled]
    
    def get_rules_for_language(self, language: str) -> List[Rule]:
        """Get all rules applicable to a language."""
        return [r for r in self.rules if r.enabled and r.matches_language(language)]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded rules."""
        return {
            'total_rules': len(self.rules),
            'enabled_rules': len([r for r in self.rules if r.enabled]),
            'disabled_rules': len([r for r in self.rules if not r.enabled]),
            'rules_by_severity': {
                'critical': len([r for r in self.rules if r.severity == 'critical']),
                'high': len([r for r in self.rules if r.severity == 'high']),
                'medium': len([r for r in self.rules if r.severity == 'medium']),
                'low': len([r for r in self.rules if r.severity == 'low']),
                'info': len([r for r in self.rules if r.severity == 'info']),
            }
        }


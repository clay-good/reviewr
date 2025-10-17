import yaml
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .engine import Rule, RulesEngine


class RulesLoader:
    """Loader for custom rules from configuration files."""
    
    @staticmethod
    def load_from_yaml(file_path: str) -> List[Rule]:
        """
        Load rules from a YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            List of Rule objects
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        return RulesLoader._parse_rules(data)
    
    @staticmethod
    def load_from_json(file_path: str) -> List[Rule]:
        """
        Load rules from a JSON file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of Rule objects
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {file_path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return RulesLoader._parse_rules(data)
    
    @staticmethod
    def load_from_dict(data: Dict[str, Any]) -> List[Rule]:
        """
        Load rules from a dictionary.
        
        Args:
            data: Dictionary containing rules
            
        Returns:
            List of Rule objects
        """
        return RulesLoader._parse_rules(data)
    
    @staticmethod
    def _parse_rules(data: Dict[str, Any]) -> List[Rule]:
        """Parse rules from dictionary data."""
        rules = []
        
        rules_list = data.get('rules', [])
        for rule_data in rules_list:
            try:
                rule = Rule(
                    id=rule_data['id'],
                    name=rule_data['name'],
                    description=rule_data.get('description', ''),
                    pattern=rule_data['pattern'],
                    severity=rule_data.get('severity', 'medium'),
                    message=rule_data['message'],
                    suggestion=rule_data.get('suggestion'),
                    languages=rule_data.get('languages'),
                    enabled=rule_data.get('enabled', True),
                    case_sensitive=rule_data.get('case_sensitive', True),
                    multiline=rule_data.get('multiline', False)
                )
                rules.append(rule)
            except KeyError as e:
                raise ValueError(f"Missing required field in rule: {e}")
        
        return rules
    
    @staticmethod
    def create_engine_from_file(file_path: str) -> RulesEngine:
        """
        Create a RulesEngine from a configuration file.
        
        Args:
            file_path: Path to YAML or JSON file
            
        Returns:
            RulesEngine with loaded rules
        """
        path = Path(file_path)
        
        if path.suffix in ['.yaml', '.yml']:
            rules = RulesLoader.load_from_yaml(file_path)
        elif path.suffix == '.json':
            rules = RulesLoader.load_from_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        return RulesEngine(rules)
    
    @staticmethod
    def get_default_rules() -> List[Rule]:
        """Get a set of default recommended rules."""
        return [
            Rule(
                id='no-hardcoded-secrets',
                name='No Hardcoded Secrets',
                description='Detect hardcoded API keys, passwords, and tokens',
                pattern=r'(?:api[_-]?key|password|secret|token)\s*[=:]\s*["\'][\w\-]{20,}["\']',
                severity='critical',
                message='Potential hardcoded secret detected',
                suggestion='Use environment variables or a secrets management system',
                case_sensitive=False
            ),
            Rule(
                id='no-todo-comments',
                name='No TODO Comments',
                description='Detect TODO comments that should be tracked',
                pattern=r'//\s*TODO:|#\s*TODO:',
                severity='info',
                message='TODO comment found',
                suggestion='Create a ticket to track this work',
                case_sensitive=False
            ),
            Rule(
                id='no-fixme-comments',
                name='No FIXME Comments',
                description='Detect FIXME comments indicating bugs',
                pattern=r'//\s*FIXME:|#\s*FIXME:',
                severity='medium',
                message='FIXME comment found',
                suggestion='Address this issue before merging',
                case_sensitive=False
            ),
            Rule(
                id='no-debugger',
                name='No Debugger Statements',
                description='Detect debugger statements in JavaScript',
                pattern=r'\bdebugger\s*;',
                severity='high',
                message='Debugger statement found',
                suggestion='Remove debugger statements before committing',
                languages=['javascript', 'typescript']
            ),
            Rule(
                id='no-print-statements',
                name='No Print Statements',
                description='Detect print statements in Python',
                pattern=r'\bprint\s*\(',
                severity='info',
                message='Print statement found',
                suggestion='Use logging instead of print statements',
                languages=['python']
            ),
            Rule(
                id='no-eval',
                name='No Eval Usage',
                description='Detect dangerous eval() usage',
                pattern=r'\beval\s*\(',
                severity='critical',
                message='Dangerous eval() usage detected',
                suggestion='Avoid eval() as it can execute arbitrary code'
            ),
            Rule(
                id='no-sql-concat',
                name='No SQL String Concatenation',
                description='Detect potential SQL injection via string concatenation',
                pattern=r'(?:SELECT|INSERT|UPDATE|DELETE).*\+.*(?:WHERE|VALUES)',
                severity='critical',
                message='Potential SQL injection via string concatenation',
                suggestion='Use parameterized queries or an ORM',
                case_sensitive=False
            ),
            Rule(
                id='no-weak-crypto',
                name='No Weak Cryptography',
                description='Detect usage of weak cryptographic algorithms',
                pattern=r'\b(?:MD5|SHA1|DES)\b',
                severity='high',
                message='Weak cryptographic algorithm detected',
                suggestion='Use SHA-256 or stronger algorithms',
                case_sensitive=False
            ),
        ]


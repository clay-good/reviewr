import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class SecretMatch:
    """A detected secret or credential."""
    type: str
    line_number: int
    column_start: int
    column_end: int
    matched_text: str
    context: str  # The line containing the match


class SecretsScanner:
    """Scanner for detecting secrets, API keys, and credentials in code."""
    
    # Regex patterns for common secrets
    PATTERNS = {
        'aws_access_key': re.compile(r'AKIA[0-9A-Z]{16}'),
        'aws_secret_key': re.compile(r'(?i)aws(.{0,20})?[\'"][0-9a-zA-Z/+]{40}[\'"]'),
        'github_token': re.compile(r'ghp_[0-9a-zA-Z]{36}'),
        'github_oauth': re.compile(r'gho_[0-9a-zA-Z]{36}'),
        'github_app': re.compile(r'(ghu|ghs)_[0-9a-zA-Z]{36}'),
        'slack_token': re.compile(r'xox[baprs]-([0-9a-zA-Z]{10,48})'),
        'slack_webhook': re.compile(r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}'),
        'google_api_key': re.compile(r'AIza[0-9A-Za-z\-_]{35}'),
        'google_oauth': re.compile(r'[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com'),
        'heroku_api_key': re.compile(r'[h|H][e|E][r|R][o|O][k|K][u|U].*[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}'),
        'mailchimp_api_key': re.compile(r'[0-9a-f]{32}-us[0-9]{1,2}'),
        'mailgun_api_key': re.compile(r'key-[0-9a-zA-Z]{32}'),
        'stripe_api_key': re.compile(r'(?:r|s)k_live_[0-9a-zA-Z]{24}'),
        'stripe_restricted_key': re.compile(r'rk_live_[0-9a-zA-Z]{24}'),
        'square_access_token': re.compile(r'sq0atp-[0-9A-Za-z\-_]{22}'),
        'square_oauth_secret': re.compile(r'sq0csp-[0-9A-Za-z\-_]{43}'),
        'paypal_braintree': re.compile(r'access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}'),
        'picatic_api_key': re.compile(r'sk_live_[0-9a-z]{32}'),
        'twilio_api_key': re.compile(r'SK[0-9a-fA-F]{32}'),
        'twilio_account_sid': re.compile(r'AC[a-zA-Z0-9_\-]{32}'),
        'twilio_app_sid': re.compile(r'AP[a-zA-Z0-9_\-]{32}'),
        'dynatrace_token': re.compile(r'dt0[a-zA-Z]{1}[0-9]{2}\.[A-Z0-9]{24}\.[A-Z0-9]{64}'),
        'shopify_shared_secret': re.compile(r'shpss_[a-fA-F0-9]{32}'),
        'shopify_access_token': re.compile(r'shpat_[a-fA-F0-9]{32}'),
        'shopify_custom_app': re.compile(r'shpca_[a-fA-F0-9]{32}'),
        'shopify_private_app': re.compile(r'shppa_[a-fA-F0-9]{32}'),
        'pypi_upload_token': re.compile(r'pypi-AgEIcHlwaS5vcmc[A-Za-z0-9-_]{50,1000}'),
        'generic_api_key': re.compile(r'(?i)(api[_-]?key|apikey|api[_-]?token|access[_-]?token|auth[_-]?token)[\'"\s]*[:=][\'"\s]*[a-zA-Z0-9_\-]{20,}'),
        'generic_secret': re.compile(r'(?i)(secret|password|passwd|pwd)[\'"\s]*[:=][\'"\s]*[^\s\'";]{8,}'),
        'private_key': re.compile(r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'),
        'jwt_token': re.compile(r'eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'),
        'basic_auth': re.compile(r'(?i)basic\s+[a-zA-Z0-9+/]{20,}={0,2}'),
        'bearer_token': re.compile(r'(?i)bearer\s+[a-zA-Z0-9_\-\.=]{20,}'),
        'connection_string': re.compile(r'(?i)(mongodb|mysql|postgresql|postgres|redis|amqp)://[^\s\'";]+:[^\s\'";]+@'),
        'database_url': re.compile(r'(?i)database[_-]?url[\'"\s]*[:=][\'"\s]*[^\s\'";]+'),
        'ssh_key': re.compile(r'ssh-(rsa|dss|ed25519)\s+AAAA[0-9A-Za-z+/]+[=]{0,3}'),
        'azure_storage_key': re.compile(r'(?i)DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{88}'),
        'facebook_access_token': re.compile(r'EAACEdEose0cBA[0-9A-Za-z]+'),
        'twitter_oauth': re.compile(r'[t|T][w|W][i|I][t|T][t|T][e|E][r|R].*[1-9][0-9]+-[0-9a-zA-Z]{40}'),
        'npm_token': re.compile(r'npm_[a-zA-Z0-9]{36}'),
        'docker_config': re.compile(r'(?i)"auth"\s*:\s*"[A-Za-z0-9+/=]{20,}"'),
    }
    
    # Patterns to exclude (common false positives)
    EXCLUDE_PATTERNS = [
        re.compile(r'example\.com'),
        re.compile(r'localhost'),
        re.compile(r'127\.0\.0\.1'),
        re.compile(r'0\.0\.0\.0'),
        re.compile(r'test[_-]?key'),
        re.compile(r'dummy[_-]?key'),
        re.compile(r'fake[_-]?key'),
        re.compile(r'sample[_-]?key'),
        re.compile(r'your[_-]?key'),
        re.compile(r'placeholder'),
        re.compile(r'xxxxxxxx'),
        re.compile(r'<.*>'),  # Template variables
        re.compile(r'\$\{.*\}'),  # Environment variable references
        re.compile(r'\{\{.*\}\}'),  # Template variables
    ]
    
    def scan_content(self, content: str, file_path: str = "") -> List[SecretMatch]:
        """
        Scan content for secrets and credentials.
        
        Args:
            content: The content to scan
            file_path: Optional file path for context
            
        Returns:
            List of detected secrets
        """
        matches = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            # Skip comments (basic detection)
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                continue
            
            # Check each pattern
            for secret_type, pattern in self.PATTERNS.items():
                for match in pattern.finditer(line):
                    matched_text = match.group(0)
                    
                    # Check if it's a false positive
                    if self._is_false_positive(matched_text, line):
                        continue
                    
                    matches.append(SecretMatch(
                        type=secret_type,
                        line_number=line_num,
                        column_start=match.start(),
                        column_end=match.end(),
                        matched_text=self._redact_secret(matched_text),
                        context=line.strip()
                    ))
        
        return matches
    
    def _is_false_positive(self, matched_text: str, context: str) -> bool:
        """Check if a match is likely a false positive."""
        # Check against exclude patterns
        for pattern in self.EXCLUDE_PATTERNS:
            if pattern.search(matched_text) or pattern.search(context):
                return True
        
        # Check if it's in a comment
        if '//' in context[:context.find(matched_text)] or '#' in context[:context.find(matched_text)]:
            return True
        
        return False
    
    def _redact_secret(self, secret: str) -> str:
        """Redact a secret for safe display."""
        if len(secret) <= 8:
            return '*' * len(secret)
        
        # Show first 4 and last 4 characters
        return f"{secret[:4]}...{secret[-4:]}"
    
    def has_secrets(self, content: str) -> bool:
        """Quick check if content contains any secrets."""
        return len(self.scan_content(content)) > 0
    
    def get_redacted_content(self, content: str) -> Tuple[str, List[SecretMatch]]:
        """
        Get content with secrets redacted.
        
        Args:
            content: The content to redact
            
        Returns:
            Tuple of (redacted_content, list of matches)
        """
        matches = self.scan_content(content)
        
        if not matches:
            return content, []
        
        # Sort matches by position (reverse order to maintain positions)
        sorted_matches = sorted(matches, key=lambda m: (m.line_number, m.column_start), reverse=True)
        
        lines = content.split('\n')
        
        for match in sorted_matches:
            line_idx = match.line_number - 1
            if 0 <= line_idx < len(lines):
                line = lines[line_idx]
                # Replace the secret with redacted version
                lines[line_idx] = (
                    line[:match.column_start] +
                    '[REDACTED]' +
                    line[match.column_end:]
                )
        
        return '\n'.join(lines), matches


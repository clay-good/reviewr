import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ..providers.base import LLMProvider, ReviewType, ReviewFinding
from ..config.schema import ReviewrConfig
from .chunker import get_chunker
from ..utils.language_detector import detect_language
from ..utils.file_discovery import discover_files
from ..utils.secrets_scanner import SecretsScanner


@dataclass
class ReviewResult:
    """Result of a code review."""
    findings: List[ReviewFinding] = field(default_factory=list)
    files_reviewed: int = 0
    total_chunks: int = 0
    provider_stats: Dict[str, Any] = field(default_factory=dict)
    
    def has_critical_issues(self) -> bool:
        """Check if there are any critical or high severity issues."""
        return any(
            f.severity in ('critical', 'high') 
            for f in self.findings
        )
    
    def get_findings_by_severity(self) -> Dict[str, List[ReviewFinding]]:
        """Group findings by severity."""
        by_severity: Dict[str, List[ReviewFinding]] = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        
        for finding in self.findings:
            if finding.severity in by_severity:
                by_severity[finding.severity].append(finding)
        
        return by_severity
    
    def get_findings_by_type(self) -> Dict[str, List[ReviewFinding]]:
        """Group findings by review type."""
        by_type: Dict[str, List[ReviewFinding]] = {}
        
        for finding in self.findings:
            type_name = finding.type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(finding)
        
        return by_type


class ReviewOrchestrator:
    """Orchestrates the code review process."""
    
    def __init__(self, provider: LLMProvider, config: ReviewrConfig, verbose: int = 0):
        """
        Initialize the orchestrator.

        Args:
            provider: LLM provider to use
            config: Configuration
            verbose: Verbosity level
        """
        self.provider = provider
        self.config = config
        self.verbose = verbose
        self.chunker = get_chunker(
            config.chunking.strategy.value,
            overlap_lines=config.chunking.overlap // 50  # Rough conversion
        )
        self.secrets_scanner = SecretsScanner()
    
    async def review_path(
        self,
        path: str,
        review_types: List[ReviewType],
        language: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> ReviewResult:
        """
        Review code at the specified path.
        
        Args:
            path: Path to file or directory
            review_types: Types of reviews to perform
            language: Optional language override
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            
        Returns:
            ReviewResult with findings
        """
        path_obj = Path(path)
        
        # Discover files to review
        if path_obj.is_file():
            files = [path_obj]
        else:
            files = discover_files(
                path_obj,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )
        
        if not files:
            return ReviewResult()
        
        # Review files
        all_findings = []
        total_chunks = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task(
                f"Reviewing {len(files)} file(s)...",
                total=len(files)
            )
            
            for file_path in files:
                try:
                    findings = await self._review_file(
                        file_path,
                        review_types,
                        language
                    )
                    all_findings.extend(findings)
                    total_chunks += 1  # Simplified for now
                    
                except Exception as e:
                    if self.verbose:
                        print(f"Error reviewing {file_path}: {e}")
                
                progress.update(task, advance=1)
        
        # Create result
        result = ReviewResult(
            findings=all_findings,
            files_reviewed=len(files),
            total_chunks=total_chunks,
            provider_stats=self.provider.get_stats()
        )
        
        return result
    
    async def _review_file(
        self,
        file_path: Path,
        review_types: List[ReviewType],
        language_override: Optional[str] = None
    ) -> List[ReviewFinding]:
        """Review a single file."""
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Skip binary files
            if self.verbose:
                print(f"Skipping binary file: {file_path}")
            return []
        except Exception as e:
            if self.verbose:
                print(f"Error reading {file_path}: {e}")
            return []
        
        # Detect language
        language = language_override or detect_language(file_path, content)

        if not language:
            if self.verbose:
                print(f"Could not detect language for: {file_path}")
            return []

        # Scan for secrets before sending to AI
        secrets_matches = self.secrets_scanner.scan_content(content, str(file_path))

        if secrets_matches:
            # Create findings for detected secrets
            secret_findings = []
            for match in secrets_matches:
                finding = ReviewFinding(
                    file_path=str(file_path),
                    line_start=match.line_number,
                    line_end=match.line_number,
                    severity='critical',
                    type=ReviewType.SECURITY,
                    message=f'Potential {match.type.replace("_", " ")} detected: {match.matched_text}',
                    suggestion='Remove hardcoded secrets and use environment variables or a secrets management system.',
                    confidence=0.9
                )
                secret_findings.append(finding)

            if self.verbose:
                print(f"Found {len(secrets_matches)} potential secret(s) in {file_path}")

            # Redact secrets from content before sending to AI
            content, _ = self.secrets_scanner.get_redacted_content(content)
        else:
            secret_findings = []

        # Chunk the file
        chunks = self.chunker.chunk_file(
            str(file_path),
            content,
            language,
            self.config.chunking.max_chunk_size
        )
        
        # Review each chunk - process review types in parallel for better performance
        all_findings = []

        for chunk in chunks:
            try:
                # Run different review types in parallel
                review_tasks = []
                for review_type in review_types:
                    task = self.provider.review_code(chunk, [review_type])
                    review_tasks.append(task)

                # Gather all results concurrently
                results = await asyncio.gather(*review_tasks, return_exceptions=True)

                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        if self.verbose:
                            print(f"Error in parallel review for {file_path}: {result}")
                        continue

                    # Filter by confidence threshold
                    filtered_findings = [
                        f for f in result
                        if f.confidence >= self.config.review.confidence_threshold
                    ]

                    all_findings.extend(filtered_findings)

            except Exception as e:
                if self.verbose:
                    print(f"Error reviewing chunk in {file_path}: {e}")

        # Add secret findings to the results
        all_findings.extend(secret_findings)

        # Limit findings per file
        if len(all_findings) > self.config.review.max_findings_per_file:
            all_findings = all_findings[:self.config.review.max_findings_per_file]

        return all_findings


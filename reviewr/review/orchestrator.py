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
from ..utils.cache import IntelligentCache
from ..analysis.analyzer_factory import AnalyzerFactory
from ..rules import RulesEngine


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

    def __init__(
        self,
        provider: Optional[LLMProvider],
        config: ReviewrConfig,
        verbose: int = 0,
        use_cache: bool = True,
        use_local_analysis: bool = True,
        rules_engine: Optional[RulesEngine] = None,
        analyzer_config: Optional[Any] = None,
        diff_analyzer: Optional[Any] = None,
        diff_base: Optional[str] = None,
        diff_target: Optional[str] = None
    ):
        """
        Initialize the orchestrator.

        Args:
            provider: LLM provider to use (None for local-only mode)
            config: Configuration
            verbose: Verbosity level
            use_cache: Whether to use intelligent caching (default: True)
            use_local_analysis: Whether to use local analysis (default: True)
            rules_engine: Optional custom rules engine
            analyzer_config: Optional configuration for advanced analyzers
            diff_analyzer: Optional diff analyzer for incremental analysis
            diff_base: Base reference for diff (e.g., 'HEAD', 'main')
            diff_target: Target reference for diff (None = working directory)
        """
        self.provider = provider
        self.config = config
        self.verbose = verbose
        self.use_cache = use_cache
        self.use_local_analysis = use_local_analysis
        self.rules_engine = rules_engine
        self.analyzer_config = analyzer_config
        self.diff_analyzer = diff_analyzer
        self.diff_base = diff_base
        self.diff_target = diff_target
        self.chunker = get_chunker(
            config.chunking.strategy.value,
            overlap_lines=config.chunking.overlap // 50  # Rough conversion
        )
        self.secrets_scanner = SecretsScanner()
        self.cache = IntelligentCache() if use_cache else None
        self.local_analysis_stats = {'findings': 0, 'files_analyzed': 0}
        self.custom_rules_stats = {'findings': 0, 'files_analyzed': 0}
    
    async def review_path(
        self,
        path: str,
        review_types: List[ReviewType],
        language: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_concurrent_files: int = 5
    ) -> ReviewResult:
        """
        Review code at the specified path.

        Args:
            path: Path to file or directory
            review_types: Types of reviews to perform
            language: Optional language override
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude
            max_concurrent_files: Maximum number of files to review concurrently

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

        # Filter to only changed files if using diff mode
        if self.diff_analyzer:
            try:
                changed_files = self.diff_analyzer.get_changed_files(
                    base_ref=self.diff_base,
                    target_ref=self.diff_target,
                    repo_path=path_obj if path_obj.is_dir() else path_obj.parent
                )

                # Convert to absolute paths for comparison
                changed_paths = {Path(f).resolve() for f in changed_files}
                files = [f for f in files if f.resolve() in changed_paths]

                if self.verbose > 0:
                    print(f"Diff mode: Reviewing {len(files)} changed file(s)")
            except Exception as e:
                if self.verbose > 0:
                    print(f"Warning: Failed to get diff, reviewing all files: {e}")

        if not files:
            return ReviewResult()

        # Review files in parallel with concurrency limit
        all_findings = []
        total_chunks = 0

        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent_files)

        async def review_with_limit(file_path):
            """Review a file with concurrency limit."""
            async with semaphore:
                return await self._review_file(file_path, review_types, language)

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

            # Create tasks for all files
            review_tasks = [review_with_limit(file_path) for file_path in files]

            # Process files in parallel
            for coro in asyncio.as_completed(review_tasks):
                try:
                    findings = await coro
                    all_findings.extend(findings)
                    total_chunks += 1  # Simplified for now

                except Exception as e:
                    if self.verbose:
                        print(f"Error reviewing file: {e}")

                progress.update(task, advance=1)

        # Create result
        result = ReviewResult(
            findings=all_findings,
            files_reviewed=len(files),
            total_chunks=total_chunks,
            provider_stats=self.provider.get_stats() if self.provider else {}
        )

        return result
    
    async def _review_file(
        self,
        file_path: Path,
        review_types: List[ReviewType],
        language_override: Optional[str] = None
    ) -> List[ReviewFinding]:
        """Review a single file."""
        # Check cache first (only if provider is available)
        if self.cache and self.provider:
            review_type_names = [rt.value for rt in review_types]
            cached_findings = self.cache.get(
                file_path,
                review_type_names,
                self.provider.name,
                self.provider.model
            )

            if cached_findings is not None:
                if self.verbose >= 2:
                    print(f"Cache hit for {file_path}")
                # Convert cached dict findings back to ReviewFinding objects
                return [ReviewFinding(**f) for f in cached_findings]

            if self.verbose >= 2:
                print(f"Cache miss for {file_path}")

        # Read file content (use diff-based content if available)
        try:
            if self.diff_analyzer:
                # Get only changed content with context
                changed_content = self.diff_analyzer.get_changed_content(
                    str(file_path),
                    base_ref=self.diff_base,
                    target_ref=self.diff_target,
                    repo_path=file_path.parent
                )

                if changed_content:
                    content = changed_content
                    if self.verbose >= 2:
                        print(f"Using diff-based content for {file_path}")
                else:
                    # No changes detected, skip file
                    if self.verbose >= 2:
                        print(f"No changes in {file_path}, skipping")
                    return []
            else:
                # Read full file content
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

        # Run local analysis first (fast, no API calls)
        local_findings = []
        if self.use_local_analysis and AnalyzerFactory.supports_language(language):
            # Pass analyzer_config if available
            analyzer = AnalyzerFactory.get_analyzer(language, self.analyzer_config)
            if analyzer:
                local_analysis_results = analyzer.analyze(str(file_path), content)
                # Convert local findings to ReviewFinding format
                local_findings = [f.to_review_finding() for f in local_analysis_results]

                if local_findings:
                    self.local_analysis_stats['findings'] += len(local_findings)
                    self.local_analysis_stats['files_analyzed'] += 1

                    if self.verbose >= 2:
                        print(f"Local analysis found {len(local_findings)} issue(s) in {file_path}")

        # Run custom rules engine (fast, no API calls)
        custom_rules_findings = []
        if self.rules_engine:
            rule_matches = self.rules_engine.analyze(str(file_path), content, language)
            # Convert rule matches to ReviewFinding format
            custom_rules_findings = [m.to_local_finding().to_review_finding() for m in rule_matches]

            if custom_rules_findings:
                self.custom_rules_stats['findings'] += len(custom_rules_findings)
                self.custom_rules_stats['files_analyzed'] += 1

                if self.verbose >= 2:
                    print(f"Custom rules found {len(custom_rules_findings)} issue(s) in {file_path}")

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

        # Review each chunk - OPTIMIZED: Single API call per chunk with all review types
        # Skip AI review if provider is None (local-only mode)
        all_findings = []

        if self.provider:
            for chunk in chunks:
                try:
                    # OPTIMIZATION: Pass all review types in a single API call
                    # This reduces API calls by 66% (for 3 review types: 3 calls -> 1 call)
                    result = await self.provider.review_code(chunk, review_types)

                    # Filter by confidence threshold
                    filtered_findings = [
                        f for f in result
                        if f.confidence >= self.config.review.confidence_threshold
                    ]

                    all_findings.extend(filtered_findings)

                except Exception as e:
                    if self.verbose:
                        print(f"Error reviewing chunk in {file_path}: {e}")

        # Add secret findings, local analysis findings, and custom rules findings to the results
        all_findings.extend(secret_findings)
        all_findings.extend(local_findings)
        all_findings.extend(custom_rules_findings)

        # Limit findings per file
        if len(all_findings) > self.config.review.max_findings_per_file:
            all_findings = all_findings[:self.config.review.max_findings_per_file]

        # Store in cache for future use (only if provider is available)
        if self.cache and self.provider:
            review_type_names = [rt.value for rt in review_types]
            # Convert findings to dicts for caching
            findings_dicts = [
                {
                    'file_path': f.file_path,
                    'line_start': f.line_start,
                    'line_end': f.line_end,
                    'severity': f.severity,
                    'type': f.type,
                    'message': f.message,
                    'suggestion': f.suggestion,
                    'confidence': f.confidence,
                    'code_snippet': f.code_snippet
                }
                for f in all_findings
            ]
            self.cache.set(
                file_path,
                review_type_names,
                self.provider.name,
                self.provider.model,
                findings_dicts
            )

        return all_findings

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics."""
        if self.cache:
            return self.cache.get_stats()
        return None

    def clear_cache(self) -> None:
        """Clear the cache."""
        if self.cache:
            self.cache.clear()

    def get_local_analysis_stats(self) -> Dict[str, Any]:
        """Get local analysis statistics."""
        return self.local_analysis_stats.copy()

    def get_custom_rules_stats(self) -> Dict[str, Any]:
        """Get custom rules statistics."""
        return self.custom_rules_stats.copy()

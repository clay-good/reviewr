
from pathlib import Path
from typing import List, Optional
import fnmatch

from .language_detector import is_code_file


# Default patterns to exclude
DEFAULT_EXCLUDE_PATTERNS = [
    '*.pyc',
    '*.pyo',
    '*.so',
    '*.dylib',
    '*.dll',
    '*.exe',
    '*.bin',
    '*.o',
    '*.a',
    '*.lib',
    '*.class',
    '*.jar',
    '*.war',
    '*.ear',
    '__pycache__',
    '.git',
    '.svn',
    '.hg',
    '.bzr',
    'node_modules',
    'venv',
    'env',
    '.venv',
    '.env',
    'dist',
    'build',
    'target',
    '.idea',
    '.vscode',
    '*.min.js',
    '*.min.css',
    '.DS_Store',
    'Thumbs.db',
]


def discover_files(
    root_path: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_file_size: int = 1024 * 1024  # 1MB default
) -> List[Path]:
    """
    Discover code files in a directory.
    
    Args:
        root_path: Root directory to search
        include_patterns: Optional list of glob patterns to include
        exclude_patterns: Optional list of glob patterns to exclude
        max_file_size: Maximum file size in bytes
        
    Returns:
        List of file paths
    """
    if not root_path.is_dir():
        return []
    
    # Combine default and custom exclude patterns
    all_exclude_patterns = DEFAULT_EXCLUDE_PATTERNS.copy()
    if exclude_patterns:
        all_exclude_patterns.extend(exclude_patterns)
    
    files = []
    
    for item in root_path.rglob('*'):
        # Skip directories
        if not item.is_file():
            continue
        
        # Skip if path matches exclude pattern
        if _matches_any_pattern(item, root_path, all_exclude_patterns):
            continue
        
        # Check include patterns if specified
        if include_patterns and not _matches_any_pattern(item, root_path, include_patterns):
            continue
        
        # Skip files that are too large
        try:
            if item.stat().st_size > max_file_size:
                continue
        except OSError:
            continue
        
        # Check if it's a code file (if no include patterns specified)
        if not include_patterns and not is_code_file(item):
            continue
        
        files.append(item)
    
    return sorted(files)


def _matches_any_pattern(file_path: Path, root_path: Path, patterns: List[str]) -> bool:
    """
    Check if a file path matches any of the given patterns.
    
    Args:
        file_path: File path to check
        root_path: Root path for relative matching
        patterns: List of glob patterns
        
    Returns:
        True if matches any pattern
    """
    try:
        relative_path = file_path.relative_to(root_path)
    except ValueError:
        relative_path = file_path
    
    path_str = str(relative_path)
    parts = relative_path.parts
    
    for pattern in patterns:
        # Check against full path
        if fnmatch.fnmatch(path_str, pattern):
            return True
        
        # Check against filename
        if fnmatch.fnmatch(file_path.name, pattern):
            return True
        
        # Check if any part of the path matches (for directory patterns)
        if any(fnmatch.fnmatch(part, pattern) for part in parts):
            return True
    
    return False


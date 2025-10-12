from pathlib import Path
from typing import Optional


# Map file extensions to language names
EXTENSION_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'zsh',
    '.sql': 'sql',
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.json': 'json',
    '.xml': 'xml',
    '.md': 'markdown',
    '.r': 'r',
    '.R': 'r',
    '.m': 'matlab',
    '.pl': 'perl',
    '.lua': 'lua',
    '.vim': 'vim',
    '.ex': 'elixir',
    '.exs': 'elixir',
    '.erl': 'erlang',
    '.hrl': 'erlang',
    '.clj': 'clojure',
    '.dart': 'dart',
}


def detect_language(file_path: Path, content: Optional[str] = None) -> Optional[str]:
    """
    Detect the programming language of a file.
    
    Args:
        file_path: Path to the file
        content: Optional file content for content-based detection
        
    Returns:
        Language name or None if not detected
    """
    # Try extension-based detection first
    suffix = file_path.suffix.lower()
    if suffix in EXTENSION_MAP:
        return EXTENSION_MAP[suffix]
    
    # Try filename-based detection
    filename = file_path.name.lower()
    
    if filename in ('makefile', 'gnumakefile'):
        return 'makefile'
    elif filename == 'dockerfile':
        return 'dockerfile'
    elif filename == 'vagrantfile':
        return 'ruby'
    elif filename == 'rakefile':
        return 'ruby'
    elif filename == 'gemfile':
        return 'ruby'
    elif filename == 'podfile':
        return 'ruby'
    
    # Try content-based detection if content is provided
    if content:
        first_line = content.split('\n')[0] if content else ''
        
        # Check for shebang
        if first_line.startswith('#!'):
            if 'python' in first_line:
                return 'python'
            elif 'node' in first_line or 'javascript' in first_line:
                return 'javascript'
            elif 'ruby' in first_line:
                return 'ruby'
            elif 'bash' in first_line or 'sh' in first_line:
                return 'bash'
            elif 'perl' in first_line:
                return 'perl'
            elif 'php' in first_line:
                return 'php'
    
    return None


def is_code_file(file_path: Path) -> bool:
    """
    Check if a file is likely a code file.
    
    Args:
        file_path: Path to check
        
    Returns:
        True if likely a code file
    """
    return detect_language(file_path) is not None


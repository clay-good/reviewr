import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from dotenv import load_dotenv

from .schema import ReviewrConfig
from .defaults import get_default_config

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for Python < 3.11
    except ImportError:
        tomllib = None  # type: ignore


class ConfigLoader:
    """Load and merge configuration from multiple sources."""
    
    def __init__(self):
        """Initialize the config loader."""
        load_dotenv()  # Load environment variables from .env file
        
    def load(
        self,
        config_path: Optional[str] = None,
        cli_overrides: Optional[Dict[str, Any]] = None,
    ) -> ReviewrConfig:
        """
        Load configuration with proper precedence.
        
        Precedence (highest to lowest):
        1. CLI arguments (cli_overrides)
        2. Environment variables (REVIEWR_*)
        3. Specified config file
        4. Project config (.reviewr.yml)
        5. User config (~/.config/reviewr/config.yml)
        6. Default values
        
        Args:
            config_path: Optional path to config file
            cli_overrides: Optional dictionary of CLI argument overrides
            
        Returns:
            Merged ReviewrConfig
        """
        # Start with defaults
        config_dict = get_default_config().model_dump()
        
        # Load user config
        user_config_path = Path.home() / ".config" / "reviewr" / "config.yml"
        if user_config_path.exists():
            user_config = self._load_yaml_file(user_config_path)
            config_dict = self._deep_merge(config_dict, user_config)
        
        # Load project config - check multiple formats
        # Priority: .reviewr.toml > .reviewr.yml > pyproject.toml
        project_config_toml = Path.cwd() / ".reviewr.toml"
        project_config_yml = Path.cwd() / ".reviewr.yml"
        pyproject_toml = Path.cwd() / "pyproject.toml"

        if project_config_toml.exists():
            project_config = self._load_toml_file(project_config_toml)
            config_dict = self._deep_merge(config_dict, project_config)
        elif project_config_yml.exists():
            project_config = self._load_yaml_file(project_config_yml)
            config_dict = self._deep_merge(config_dict, project_config)
        elif pyproject_toml.exists():
            # Load from [tool.reviewr] section
            project_config = self._load_pyproject_toml(pyproject_toml)
            if project_config:
                config_dict = self._deep_merge(config_dict, project_config)
        
        # Load specified config file
        if config_path:
            specified_config = self._load_yaml_file(Path(config_path))
            config_dict = self._deep_merge(config_dict, specified_config)
        
        # Apply environment variable overrides
        env_overrides = self._load_env_overrides()
        config_dict = self._deep_merge(config_dict, env_overrides)
        
        # Apply CLI overrides
        if cli_overrides:
            config_dict = self._deep_merge(config_dict, cli_overrides)
        
        # Validate and return
        return ReviewrConfig(**config_dict)
    
    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """Load and parse YAML file with environment variable expansion."""
        with open(path, 'r') as f:
            content = f.read()

        # Expand environment variables
        content = self._expand_env_vars(content)

        # Parse YAML
        data = yaml.safe_load(content)
        return data or {}

    def _load_toml_file(self, path: Path) -> Dict[str, Any]:
        """Load and parse TOML file."""
        if tomllib is None:
            raise ImportError("TOML support requires Python 3.11+ or 'tomli' package. Install with: pip install tomli")

        with open(path, 'rb') as f:
            data = tomllib.load(f)

        return data or {}

    def _load_pyproject_toml(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load reviewr configuration from pyproject.toml [tool.reviewr] section."""
        if tomllib is None:
            return None

        with open(path, 'rb') as f:
            data = tomllib.load(f)

        # Extract [tool.reviewr] section
        return data.get('tool', {}).get('reviewr', {})
    
    def _expand_env_vars(self, content: str) -> str:
        """Expand ${VAR} and $VAR style environment variables."""
        def replace_var(match: re.Match) -> str:
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, match.group(0))
        
        # Replace ${VAR} and $VAR patterns
        content = re.sub(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)', replace_var, content)
        return content
    
    def _load_env_overrides(self) -> Dict[str, Any]:
        """Load configuration overrides from environment variables."""
        overrides: Dict[str, Any] = {}
        
        # Check for provider API keys
        providers: Dict[str, Any] = {}
        
        if api_key := os.environ.get('ANTHROPIC_API_KEY'):
            providers['claude'] = {'api_key': api_key}
        
        if api_key := os.environ.get('OPENAI_API_KEY'):
            providers['openai'] = {'api_key': api_key}
        
        if api_key := os.environ.get('GOOGLE_API_KEY'):
            providers['gemini'] = {'api_key': api_key}
        
        if providers:
            overrides['providers'] = providers
        
        # Check for other REVIEWR_* environment variables
        if default_provider := os.environ.get('REVIEWR_DEFAULT_PROVIDER'):
            overrides['default_provider'] = default_provider
        
        if cache_enabled := os.environ.get('REVIEWR_CACHE_ENABLED'):
            overrides.setdefault('cache', {})['enabled'] = cache_enabled.lower() in ('true', '1', 'yes')
        
        return overrides
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save_template(self, path: Path) -> None:
        """Save a template configuration file."""
        from .defaults import DEFAULT_CONFIG_TEMPLATE
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(DEFAULT_CONFIG_TEMPLATE)


"""
Configuration presets for common use cases.

Provides predefined configurations for:
- Security-focused reviews
- Performance-focused reviews
- Quick scans
- Comprehensive reviews
- Team-specific presets
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import yaml
import json
from pathlib import Path


@dataclass
class PresetConfig:
    """Configuration preset."""
    
    name: str
    description: str
    review_types: List[str]
    min_severity: str = "info"
    enabled_analyzers: List[str] = field(default_factory=list)
    disabled_analyzers: List[str] = field(default_factory=list)
    max_findings: Optional[int] = None
    fail_on_critical: bool = True
    fail_on_high_threshold: Optional[int] = None
    custom_rules: Optional[str] = None
    output_format: str = "markdown"
    additional_options: Dict[str, Any] = field(default_factory=dict)


# Predefined presets
PRESETS: Dict[str, PresetConfig] = {
    "security": PresetConfig(
        name="security",
        description="Security-focused review: vulnerabilities, injections, auth issues",
        review_types=["security"],
        min_severity="medium",
        enabled_analyzers=["security", "dataflow", "semantic"],
        fail_on_critical=True,
        fail_on_high_threshold=0,
        additional_options={
            "enable_secrets_detection": True,
            "enable_dependency_scan": True,
        }
    ),
    
    "performance": PresetConfig(
        name="performance",
        description="Performance-focused review: bottlenecks, inefficiencies, optimization opportunities",
        review_types=["performance"],
        min_severity="medium",
        enabled_analyzers=["performance", "complexity", "dataflow"],
        fail_on_critical=False,
        fail_on_high_threshold=5,
        additional_options={
            "enable_profiling": True,
            "check_algorithmic_complexity": True,
        }
    ),
    
    "quick": PresetConfig(
        name="quick",
        description="Quick scan: fast review focusing on critical issues only",
        review_types=["security", "correctness"],
        min_severity="high",
        enabled_analyzers=["security"],
        max_findings=20,
        fail_on_critical=True,
        additional_options={
            "fast_mode": True,
            "skip_ai_review": False,
            "local_only": False,
        }
    ),
    
    "comprehensive": PresetConfig(
        name="comprehensive",
        description="Comprehensive review: all review types and analyzers",
        review_types=["security", "performance", "correctness", "maintainability", "architecture", "standards"],
        min_severity="info",
        enabled_analyzers=["security", "dataflow", "complexity", "type", "performance", "semantic"],
        fail_on_critical=True,
        fail_on_high_threshold=10,
        additional_options={
            "enable_all_checks": True,
            "detailed_reports": True,
        }
    ),
    
    "maintainability": PresetConfig(
        name="maintainability",
        description="Code quality and maintainability: complexity, documentation, best practices",
        review_types=["maintainability", "standards"],
        min_severity="low",
        enabled_analyzers=["complexity", "semantic", "type"],
        fail_on_critical=False,
        additional_options={
            "check_documentation": True,
            "check_test_coverage": True,
            "check_code_smells": True,
        }
    ),
    
    "pre-commit": PresetConfig(
        name="pre-commit",
        description="Pre-commit hook: fast, focused on blocking issues",
        review_types=["security", "correctness"],
        min_severity="high",
        enabled_analyzers=["security", "dataflow"],
        max_findings=10,
        fail_on_critical=True,
        output_format="sarif",
        additional_options={
            "fast_mode": True,
            "timeout": 30,
        }
    ),
    
    "ci-cd": PresetConfig(
        name="ci-cd",
        description="CI/CD pipeline: balanced review for pull requests",
        review_types=["security", "performance", "correctness", "maintainability"],
        min_severity="medium",
        enabled_analyzers=["security", "dataflow", "complexity", "performance"],
        max_findings=50,
        fail_on_critical=True,
        fail_on_high_threshold=5,
        output_format="sarif",
        additional_options={
            "post_pr_comment": True,
            "update_status_check": True,
        }
    ),
    
    "strict": PresetConfig(
        name="strict",
        description="Strict mode: zero tolerance for issues",
        review_types=["security", "performance", "correctness", "maintainability", "architecture", "standards"],
        min_severity="low",
        enabled_analyzers=["security", "dataflow", "complexity", "type", "performance", "semantic"],
        fail_on_critical=True,
        fail_on_high_threshold=0,
        additional_options={
            "strict_mode": True,
            "fail_on_warnings": True,
        }
    ),
}


class PresetManager:
    """Manage configuration presets."""
    
    def __init__(self, custom_presets_dir: Optional[Path] = None):
        """
        Initialize preset manager.
        
        Args:
            custom_presets_dir: Directory containing custom preset files
        """
        self.presets = PRESETS.copy()
        self.custom_presets_dir = custom_presets_dir
        
        if custom_presets_dir and custom_presets_dir.exists():
            self._load_custom_presets()
    
    def _load_custom_presets(self):
        """Load custom presets from directory."""
        if not self.custom_presets_dir:
            return

        # Load YAML files
        for preset_file in self.custom_presets_dir.glob("*.yml"):
            try:
                preset = self._load_preset_file(preset_file)
                if preset:
                    self.presets[preset.name] = preset
            except Exception as e:
                print(f"Warning: Failed to load preset from {preset_file}: {e}")

        for preset_file in self.custom_presets_dir.glob("*.yaml"):
            try:
                preset = self._load_preset_file(preset_file)
                if preset:
                    self.presets[preset.name] = preset
            except Exception as e:
                print(f"Warning: Failed to load preset from {preset_file}: {e}")

        # Load JSON files
        for preset_file in self.custom_presets_dir.glob("*.json"):
            try:
                preset = self._load_preset_file(preset_file)
                if preset:
                    self.presets[preset.name] = preset
            except Exception as e:
                print(f"Warning: Failed to load preset from {preset_file}: {e}")
    
    def _load_preset_file(self, file_path: Path) -> Optional[PresetConfig]:
        """Load preset from file."""
        with open(file_path, 'r') as f:
            if file_path.suffix in ['.yml', '.yaml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        if not data or 'name' not in data:
            return None
        
        return PresetConfig(
            name=data['name'],
            description=data.get('description', ''),
            review_types=data.get('review_types', []),
            min_severity=data.get('min_severity', 'info'),
            enabled_analyzers=data.get('enabled_analyzers', []),
            disabled_analyzers=data.get('disabled_analyzers', []),
            max_findings=data.get('max_findings'),
            fail_on_critical=data.get('fail_on_critical', True),
            fail_on_high_threshold=data.get('fail_on_high_threshold'),
            custom_rules=data.get('custom_rules'),
            output_format=data.get('output_format', 'markdown'),
            additional_options=data.get('additional_options', {})
        )
    
    def get_preset(self, name: str) -> Optional[PresetConfig]:
        """Get preset by name."""
        return self.presets.get(name)
    
    def list_presets(self) -> List[str]:
        """List all available preset names."""
        return list(self.presets.keys())
    
    def get_preset_description(self, name: str) -> Optional[str]:
        """Get preset description."""
        preset = self.presets.get(name)
        return preset.description if preset else None
    
    def apply_preset(self, name: str, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply preset to base configuration.
        
        Args:
            name: Preset name
            base_config: Base configuration dict
            
        Returns:
            Updated configuration dict
        """
        preset = self.get_preset(name)
        if not preset:
            raise ValueError(f"Unknown preset: {name}")
        
        # Create new config from preset
        config = base_config.copy()
        
        # Apply preset values
        config['review_types'] = preset.review_types
        config['min_severity'] = preset.min_severity
        config['output_format'] = preset.output_format
        
        if preset.enabled_analyzers:
            config['enabled_analyzers'] = preset.enabled_analyzers
        if preset.disabled_analyzers:
            config['disabled_analyzers'] = preset.disabled_analyzers
        if preset.max_findings is not None:
            config['max_findings'] = preset.max_findings
        if preset.fail_on_critical is not None:
            config['fail_on_critical'] = preset.fail_on_critical
        if preset.fail_on_high_threshold is not None:
            config['fail_on_high_threshold'] = preset.fail_on_high_threshold
        if preset.custom_rules:
            config['custom_rules'] = preset.custom_rules
        
        # Merge additional options
        config.update(preset.additional_options)
        
        return config
    
    def save_preset(self, preset: PresetConfig, file_path: Path):
        """Save preset to file."""
        data = {
            'name': preset.name,
            'description': preset.description,
            'review_types': preset.review_types,
            'min_severity': preset.min_severity,
            'enabled_analyzers': preset.enabled_analyzers,
            'disabled_analyzers': preset.disabled_analyzers,
            'max_findings': preset.max_findings,
            'fail_on_critical': preset.fail_on_critical,
            'fail_on_high_threshold': preset.fail_on_high_threshold,
            'custom_rules': preset.custom_rules,
            'output_format': preset.output_format,
            'additional_options': preset.additional_options,
        }
        
        with open(file_path, 'w') as f:
            if file_path.suffix in ['.yml', '.yaml']:
                yaml.dump(data, f, default_flow_style=False)
            else:
                json.dump(data, f, indent=2)


# Global preset manager instance
_preset_manager = None


def get_preset_manager(custom_presets_dir: Optional[Path] = None) -> PresetManager:
    """Get global preset manager instance."""
    global _preset_manager
    if _preset_manager is None:
        _preset_manager = PresetManager(custom_presets_dir)
    return _preset_manager


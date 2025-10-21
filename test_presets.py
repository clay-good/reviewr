"""
Tests for configuration presets system.
"""

import pytest
from pathlib import Path
import tempfile
import yaml
import json

from reviewr.config.presets import (
    PresetConfig,
    PresetManager,
    get_preset_manager,
    PRESETS
)


def test_builtin_presets_exist():
    """Test that all built-in presets are defined."""
    expected_presets = [
        'security', 'performance', 'quick', 'comprehensive',
        'maintainability', 'pre-commit', 'ci-cd', 'strict'
    ]
    
    for preset_name in expected_presets:
        assert preset_name in PRESETS, f"Missing preset: {preset_name}"
        preset = PRESETS[preset_name]
        assert isinstance(preset, PresetConfig)
        assert preset.name == preset_name
        assert preset.description
        assert preset.review_types


def test_security_preset():
    """Test security preset configuration."""
    preset = PRESETS['security']
    
    assert preset.name == 'security'
    assert 'security' in preset.review_types
    assert preset.min_severity == 'medium'
    assert 'security' in preset.enabled_analyzers
    assert preset.fail_on_critical is True
    assert preset.fail_on_high_threshold == 0
    assert preset.additional_options.get('enable_secrets_detection') is True


def test_performance_preset():
    """Test performance preset configuration."""
    preset = PRESETS['performance']
    
    assert preset.name == 'performance'
    assert 'performance' in preset.review_types
    assert preset.min_severity == 'medium'
    assert 'performance' in preset.enabled_analyzers
    assert preset.fail_on_critical is False
    assert preset.fail_on_high_threshold == 5


def test_quick_preset():
    """Test quick scan preset configuration."""
    preset = PRESETS['quick']
    
    assert preset.name == 'quick'
    assert 'security' in preset.review_types
    assert 'correctness' in preset.review_types
    assert preset.min_severity == 'high'
    assert preset.max_findings == 20
    assert preset.additional_options.get('fast_mode') is True


def test_comprehensive_preset():
    """Test comprehensive preset configuration."""
    preset = PRESETS['comprehensive']
    
    assert preset.name == 'comprehensive'
    assert len(preset.review_types) == 6
    assert 'security' in preset.review_types
    assert 'performance' in preset.review_types
    assert 'correctness' in preset.review_types
    assert 'maintainability' in preset.review_types
    assert 'architecture' in preset.review_types
    assert 'standards' in preset.review_types
    assert preset.min_severity == 'info'


def test_preset_manager_get_preset():
    """Test getting presets from manager."""
    manager = PresetManager()
    
    # Test getting existing preset
    preset = manager.get_preset('security')
    assert preset is not None
    assert preset.name == 'security'
    
    # Test getting non-existent preset
    preset = manager.get_preset('nonexistent')
    assert preset is None


def test_preset_manager_list_presets():
    """Test listing all presets."""
    manager = PresetManager()
    presets = manager.list_presets()
    
    assert len(presets) >= 8
    assert 'security' in presets
    assert 'performance' in presets
    assert 'quick' in presets


def test_preset_manager_apply_preset():
    """Test applying preset to configuration."""
    manager = PresetManager()
    base_config = {
        'default_provider': 'claude',
        'output_format': 'sarif'
    }
    
    # Apply security preset
    config = manager.apply_preset('security', base_config)
    
    assert config['review_types'] == ['security']
    assert config['min_severity'] == 'medium'
    assert config['fail_on_critical'] is True
    assert config['fail_on_high_threshold'] == 0
    assert config['enable_secrets_detection'] is True
    
    # Original config should not be modified
    assert 'review_types' not in base_config


def test_preset_manager_save_and_load_yaml():
    """Test saving and loading preset from YAML file."""
    manager = PresetManager()
    
    custom_preset = PresetConfig(
        name='custom-security',
        description='Custom security preset',
        review_types=['security', 'correctness'],
        min_severity='high',
        enabled_analyzers=['security', 'dataflow'],
        fail_on_critical=True,
        output_format='sarif'
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'custom-security.yml'
        
        # Save preset
        manager.save_preset(custom_preset, file_path)
        assert file_path.exists()
        
        # Load and verify
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data['name'] == 'custom-security'
        assert data['description'] == 'Custom security preset'
        assert data['review_types'] == ['security', 'correctness']
        assert data['min_severity'] == 'high'


def test_preset_manager_save_and_load_json():
    """Test saving and loading preset from JSON file."""
    manager = PresetManager()
    
    custom_preset = PresetConfig(
        name='custom-performance',
        description='Custom performance preset',
        review_types=['performance'],
        min_severity='medium',
        enabled_analyzers=['performance', 'complexity'],
        fail_on_critical=False,
        output_format='markdown'
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / 'custom-performance.json'
        
        # Save preset
        manager.save_preset(custom_preset, file_path)
        assert file_path.exists()
        
        # Load and verify
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        assert data['name'] == 'custom-performance'
        assert data['description'] == 'Custom performance preset'
        assert data['review_types'] == ['performance']


def test_preset_manager_load_custom_presets():
    """Test loading custom presets from directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create custom preset file
        custom_preset_data = {
            'name': 'team-standard',
            'description': 'Team standard preset',
            'review_types': ['security', 'maintainability'],
            'min_severity': 'medium',
            'enabled_analyzers': ['security', 'complexity'],
            'fail_on_critical': True,
            'output_format': 'markdown'
        }
        
        with open(tmpdir_path / 'team-standard.yml', 'w') as f:
            yaml.dump(custom_preset_data, f)
        
        # Create manager with custom presets directory
        manager = PresetManager(custom_presets_dir=tmpdir_path)
        
        # Verify custom preset is loaded
        assert 'team-standard' in manager.list_presets()
        preset = manager.get_preset('team-standard')
        assert preset is not None
        assert preset.name == 'team-standard'
        assert preset.description == 'Team standard preset'


def test_preset_manager_apply_unknown_preset():
    """Test applying unknown preset raises error."""
    manager = PresetManager()
    
    with pytest.raises(ValueError, match="Unknown preset"):
        manager.apply_preset('nonexistent', {})


def test_get_preset_manager_singleton():
    """Test that get_preset_manager returns singleton instance."""
    manager1 = get_preset_manager()
    manager2 = get_preset_manager()
    
    # Should return same instance
    assert manager1 is manager2


def test_preset_config_defaults():
    """Test PresetConfig default values."""
    preset = PresetConfig(
        name='test',
        description='Test preset',
        review_types=['security']
    )
    
    assert preset.min_severity == 'info'
    assert preset.enabled_analyzers == []
    assert preset.disabled_analyzers == []
    assert preset.max_findings is None
    assert preset.fail_on_critical is True
    assert preset.fail_on_high_threshold is None
    assert preset.custom_rules is None
    assert preset.output_format == 'markdown'
    assert preset.additional_options == {}


def test_all_presets_have_required_fields():
    """Test that all built-in presets have required fields."""
    for name, preset in PRESETS.items():
        assert preset.name == name
        assert preset.description
        assert len(preset.review_types) > 0
        assert preset.min_severity in ['info', 'low', 'medium', 'high', 'critical']
        assert preset.output_format in ['sarif', 'markdown', 'html', 'junit']
        assert isinstance(preset.fail_on_critical, bool)
        assert isinstance(preset.additional_options, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


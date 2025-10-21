"""
CLI commands for managing configuration presets.
"""

import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from reviewr.config.presets import get_preset_manager, PresetConfig


console = Console()


@click.group(name='preset')
def preset_cli():
    """Manage configuration presets."""
    pass


@preset_cli.command(name='list')
@click.option('--custom-dir', type=click.Path(exists=True, file_okay=False, path_type=Path),
              help='Directory containing custom presets')
def list_presets(custom_dir: Optional[Path]):
    """List all available presets."""
    manager = get_preset_manager(custom_dir)
    
    table = Table(title="📋 Available Configuration Presets", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", width=20)
    table.add_column("Description", style="white", width=60)
    table.add_column("Review Types", style="yellow", width=30)
    
    for name in sorted(manager.list_presets()):
        preset = manager.get_preset(name)
        if preset:
            review_types = ", ".join(preset.review_types[:3])
            if len(preset.review_types) > 3:
                review_types += f" +{len(preset.review_types) - 3} more"
            table.add_row(name, preset.description, review_types)
    
    console.print(table)
    console.print("\n💡 Use: [cyan]reviewr --preset <name>[/cyan] to use a preset")
    console.print("💡 Use: [cyan]reviewr preset show <name>[/cyan] to see preset details")


@preset_cli.command(name='show')
@click.argument('name')
@click.option('--custom-dir', type=click.Path(exists=True, file_okay=False, path_type=Path),
              help='Directory containing custom presets')
def show_preset(name: str, custom_dir: Optional[Path]):
    """Show detailed information about a preset."""
    manager = get_preset_manager(custom_dir)
    preset = manager.get_preset(name)
    
    if not preset:
        console.print(f"[red]❌ Preset '{name}' not found[/red]")
        console.print(f"\n💡 Use: [cyan]reviewr preset list[/cyan] to see available presets")
        return
    
    # Create detailed view
    details = f"""
# {preset.name}

**Description:** {preset.description}

## Configuration

**Review Types:** {', '.join(preset.review_types)}

**Minimum Severity:** {preset.min_severity}

**Output Format:** {preset.output_format}

**Fail on Critical:** {'✅ Yes' if preset.fail_on_critical else '❌ No'}

**Fail on High Threshold:** {preset.fail_on_high_threshold if preset.fail_on_high_threshold is not None else 'Not set'}

**Max Findings:** {preset.max_findings if preset.max_findings is not None else 'Unlimited'}

## Analyzers

**Enabled:** {', '.join(preset.enabled_analyzers) if preset.enabled_analyzers else 'All'}

**Disabled:** {', '.join(preset.disabled_analyzers) if preset.disabled_analyzers else 'None'}

## Additional Options

"""
    
    if preset.additional_options:
        for key, value in preset.additional_options.items():
            details += f"- **{key}:** {value}\n"
    else:
        details += "None\n"
    
    details += f"""
## Usage

```bash
# Use this preset
reviewr <file_or_dir> --preset {preset.name}

# Combine with other options
reviewr <file_or_dir> --preset {preset.name} --output-format html

# Use in CI/CD
reviewr . --preset {preset.name} --fail-on-critical
```
"""
    
    console.print(Panel(Markdown(details), title=f"Preset: {preset.name}", border_style="cyan"))


@preset_cli.command(name='create')
@click.argument('name')
@click.option('--description', required=True, help='Preset description')
@click.option('--review-types', required=True, help='Comma-separated review types')
@click.option('--min-severity', default='info', help='Minimum severity level')
@click.option('--output-format', default='markdown', help='Output format')
@click.option('--fail-on-critical/--no-fail-on-critical', default=True, help='Fail on critical issues')
@click.option('--fail-on-high-threshold', type=int, help='Fail if high issues exceed threshold')
@click.option('--max-findings', type=int, help='Maximum findings to report')
@click.option('--enabled-analyzers', help='Comma-separated list of enabled analyzers')
@click.option('--output', type=click.Path(path_type=Path), required=True, help='Output file path')
def create_preset(
    name: str,
    description: str,
    review_types: str,
    min_severity: str,
    output_format: str,
    fail_on_critical: bool,
    fail_on_high_threshold: Optional[int],
    max_findings: Optional[int],
    enabled_analyzers: Optional[str],
    output: Path
):
    """Create a custom preset."""
    review_types_list = [rt.strip() for rt in review_types.split(',')]
    enabled_analyzers_list = [a.strip() for a in enabled_analyzers.split(',')] if enabled_analyzers else []
    
    preset = PresetConfig(
        name=name,
        description=description,
        review_types=review_types_list,
        min_severity=min_severity,
        enabled_analyzers=enabled_analyzers_list,
        max_findings=max_findings,
        fail_on_critical=fail_on_critical,
        fail_on_high_threshold=fail_on_high_threshold,
        output_format=output_format
    )
    
    manager = get_preset_manager()
    
    try:
        manager.save_preset(preset, output)
        console.print(f"[green]✅ Preset '{name}' created successfully![/green]")
        console.print(f"📁 Saved to: {output}")
        console.print(f"\n💡 Use: [cyan]reviewr --preset {name} --custom-presets-dir {output.parent}[/cyan]")
    except Exception as e:
        console.print(f"[red]❌ Failed to create preset: {e}[/red]")


@preset_cli.command(name='export')
@click.argument('name')
@click.option('--output', type=click.Path(path_type=Path), required=True, help='Output file path')
@click.option('--custom-dir', type=click.Path(exists=True, file_okay=False, path_type=Path),
              help='Directory containing custom presets')
def export_preset(name: str, output: Path, custom_dir: Optional[Path]):
    """Export a preset to a file."""
    manager = get_preset_manager(custom_dir)
    preset = manager.get_preset(name)
    
    if not preset:
        console.print(f"[red]❌ Preset '{name}' not found[/red]")
        return
    
    try:
        manager.save_preset(preset, output)
        console.print(f"[green]✅ Preset '{name}' exported successfully![/green]")
        console.print(f"📁 Saved to: {output}")
    except Exception as e:
        console.print(f"[red]❌ Failed to export preset: {e}[/red]")


@preset_cli.command(name='compare')
@click.argument('preset1')
@click.argument('preset2')
@click.option('--custom-dir', type=click.Path(exists=True, file_okay=False, path_type=Path),
              help='Directory containing custom presets')
def compare_presets(preset1: str, preset2: str, custom_dir: Optional[Path]):
    """Compare two presets side-by-side."""
    manager = get_preset_manager(custom_dir)
    
    p1 = manager.get_preset(preset1)
    p2 = manager.get_preset(preset2)
    
    if not p1:
        console.print(f"[red]❌ Preset '{preset1}' not found[/red]")
        return
    if not p2:
        console.print(f"[red]❌ Preset '{preset2}' not found[/red]")
        return
    
    table = Table(title=f"Comparing: {preset1} vs {preset2}", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", width=25)
    table.add_column(preset1, style="yellow", width=35)
    table.add_column(preset2, style="green", width=35)
    
    # Compare properties
    table.add_row("Description", p1.description, p2.description)
    table.add_row("Review Types", ", ".join(p1.review_types), ", ".join(p2.review_types))
    table.add_row("Min Severity", p1.min_severity, p2.min_severity)
    table.add_row("Output Format", p1.output_format, p2.output_format)
    table.add_row("Fail on Critical", "✅" if p1.fail_on_critical else "❌", "✅" if p2.fail_on_critical else "❌")
    table.add_row("High Threshold", str(p1.fail_on_high_threshold or "None"), str(p2.fail_on_high_threshold or "None"))
    table.add_row("Max Findings", str(p1.max_findings or "Unlimited"), str(p2.max_findings or "Unlimited"))
    table.add_row("Enabled Analyzers", ", ".join(p1.enabled_analyzers) or "All", ", ".join(p2.enabled_analyzers) or "All")
    
    console.print(table)


if __name__ == '__main__':
    preset_cli()


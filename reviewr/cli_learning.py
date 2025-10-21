"""
CLI commands for learning mode and feedback management.
"""

import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from reviewr.learning import (
    FeedbackStore,
    FeedbackType,
    FeedbackReason,
    FindingFeedback,
    LearningModel,
    LearningConfig
)


console = Console()


@click.group(name='learn')
def learning_cli():
    """Manage learning mode and feedback."""
    pass


@learning_cli.command(name='init')
@click.option('--db-path', type=click.Path(path_type=Path), default=Path('.reviewr/feedback.db'),
              help='Path to feedback database')
def init_feedback_db(db_path: Path):
    """Initialize feedback database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Initializing feedback database...", total=None)
        store = FeedbackStore(db_path)
        progress.update(task, completed=True)
    
    console.print(f"[green]✅ Feedback database initialized at {db_path}[/green]")


@learning_cli.command(name='stats')
@click.option('--db-path', type=click.Path(exists=True, path_type=Path), default=Path('.reviewr/feedback.db'),
              help='Path to feedback database')
@click.option('--rule-id', help='Show stats for specific rule')
def show_stats(db_path: Path, rule_id: Optional[str]):
    """Show feedback statistics."""
    store = FeedbackStore(db_path)
    stats = store.get_feedback_stats(rule_id)
    
    if rule_id:
        console.print(Panel(f"Feedback Statistics for Rule: [cyan]{rule_id}[/cyan]", style="bold magenta"))
    else:
        console.print(Panel("Overall Feedback Statistics", style="bold magenta"))
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="yellow", width=30)
    table.add_column("Value", style="white", width=20)
    
    table.add_row("Total Feedback", str(stats['total']))
    table.add_row("Accepted", f"{stats['accept']} ({stats['accept_rate']:.1%})")
    table.add_row("Rejected", f"{stats['reject']} ({stats['reject_rate']:.1%})")
    table.add_row("Modified", str(stats['modify']))
    table.add_row("Skipped", str(stats['skip']))
    
    console.print(table)


@learning_cli.command(name='false-positives')
@click.option('--db-path', type=click.Path(exists=True, path_type=Path), default=Path('.reviewr/feedback.db'),
              help='Path to feedback database')
@click.option('--threshold', type=float, default=0.5, help='Minimum reject rate (0.0-1.0)')
def show_false_positives(db_path: Path, threshold: float):
    """Show rules with high false positive rate."""
    store = FeedbackStore(db_path)
    rules = store.get_false_positive_rules(threshold)
    
    if not rules:
        console.print(f"[green]✅ No rules with reject rate >= {threshold:.0%}[/green]")
        return
    
    console.print(f"\n[yellow]⚠️  Rules with reject rate >= {threshold:.0%}:[/yellow]\n")
    
    table = Table(show_header=True, header_style="bold red")
    table.add_column("Rule ID", style="cyan", width=40)
    table.add_column("Reject Rate", style="red", width=15)
    table.add_column("Total Feedback", style="white", width=15)
    
    for rule_id in rules:
        stats = store.get_feedback_stats(rule_id)
        table.add_row(
            rule_id,
            f"{stats['reject_rate']:.1%}",
            str(stats['total'])
        )
    
    console.print(table)
    console.print(f"\n💡 Consider suppressing these rules or adjusting their configuration")


@learning_cli.command(name='adjustments')
@click.option('--db-path', type=click.Path(exists=True, path_type=Path), default=Path('.reviewr/feedback.db'),
              help='Path to feedback database')
@click.option('--min-feedback', type=int, default=5, help='Minimum feedback count')
def show_adjustments(db_path: Path, min_feedback: int):
    """Show learned rule adjustments."""
    store = FeedbackStore(db_path)
    config = LearningConfig(min_feedback_count=min_feedback)
    model = LearningModel(store, config)
    
    stats = model.get_learning_stats()
    
    console.print(Panel("Learning Model Statistics", style="bold magenta"))
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="yellow", width=30)
    table.add_column("Value", style="white", width=20)
    
    table.add_row("Rules with Feedback", str(stats['total_rules_with_feedback']))
    table.add_row("Suppressed Rules", str(stats['suppressed_rules']))
    table.add_row("Adjusted Severities", str(stats['adjusted_severities']))
    table.add_row("Average Accept Rate", f"{stats['average_accept_rate']:.1%}")
    table.add_row("Average Reject Rate", f"{stats['average_reject_rate']:.1%}")
    table.add_row("Total Feedback", str(stats['total_feedback']))
    
    console.print(table)
    
    # Show adjustments
    if model.rule_adjustments:
        console.print("\n[bold cyan]Rule Adjustments:[/bold cyan]\n")
        
        adj_table = Table(show_header=True, header_style="bold magenta")
        adj_table.add_column("Rule ID", style="cyan", width=30)
        adj_table.add_column("Original", style="yellow", width=12)
        adj_table.add_column("Adjusted", style="green", width=12)
        adj_table.add_column("Status", style="white", width=15)
        adj_table.add_column("Accept Rate", style="white", width=12)
        
        for adj in model.rule_adjustments.values():
            status = "🚫 Suppressed" if adj.suppress else "✅ Active"
            adjusted = adj.adjusted_severity or adj.original_severity
            
            adj_table.add_row(
                adj.rule_id[:30],
                adj.original_severity,
                adjusted,
                status,
                f"{adj.accept_rate:.1%}"
            )
        
        console.print(adj_table)


@learning_cli.command(name='recommendations')
@click.option('--db-path', type=click.Path(exists=True, path_type=Path), default=Path('.reviewr/feedback.db'),
              help='Path to feedback database')
@click.option('--min-feedback', type=int, default=5, help='Minimum feedback count')
def show_recommendations(db_path: Path, min_feedback: int):
    """Show recommendations for improving review quality."""
    store = FeedbackStore(db_path)
    config = LearningConfig(min_feedback_count=min_feedback)
    model = LearningModel(store, config)
    
    recommendations = model.get_recommendations()
    
    if not recommendations:
        console.print("[green]✅ No recommendations - review quality looks good![/green]")
        return
    
    console.print(f"\n[bold cyan]📋 Recommendations ({len(recommendations)}):[/bold cyan]\n")
    
    for i, rec in enumerate(recommendations, 1):
        if rec['type'] == 'high_false_positive':
            icon = "🔴"
            color = "red"
        else:
            icon = "🟡"
            color = "yellow"
        
        console.print(f"{icon} [{color}]{rec['recommendation']}[/{color}]")


@learning_cli.command(name='export')
@click.option('--db-path', type=click.Path(exists=True, path_type=Path), default=Path('.reviewr/feedback.db'),
              help='Path to feedback database')
@click.option('--output', type=click.Path(path_type=Path), required=True, help='Output file path')
@click.option('--format', type=click.Choice(['feedback', 'adjustments']), default='feedback',
              help='Export format')
def export_data(db_path: Path, output: Path, format: str):
    """Export feedback or adjustments to JSON."""
    store = FeedbackStore(db_path)
    
    if format == 'feedback':
        store.export_feedback(output)
        console.print(f"[green]✅ Feedback exported to {output}[/green]")
    else:
        config = LearningConfig()
        model = LearningModel(store, config)
        model.export_adjustments(output)
        console.print(f"[green]✅ Adjustments exported to {output}[/green]")


@learning_cli.command(name='enable')
@click.option('--config-file', type=click.Path(path_type=Path), default=Path('.reviewr.yml'),
              help='Configuration file to update')
def enable_learning(config_file: Path):
    """Enable learning mode in configuration."""
    import yaml
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}
    
    config['learning'] = {
        'enabled': True,
        'feedback_db': '.reviewr/feedback.db',
        'min_feedback_count': 5,
        'false_positive_threshold': 0.6,
        'apply_adjustments': True
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    console.print(f"[green]✅ Learning mode enabled in {config_file}[/green]")
    console.print("\n💡 Run [cyan]reviewr learn init[/cyan] to initialize the feedback database")


@learning_cli.command(name='disable')
@click.option('--config-file', type=click.Path(exists=True, path_type=Path), default=Path('.reviewr.yml'),
              help='Configuration file to update')
def disable_learning(config_file: Path):
    """Disable learning mode in configuration."""
    import yaml
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f) or {}
    
    if 'learning' in config:
        config['learning']['enabled'] = False
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        console.print(f"[green]✅ Learning mode disabled in {config_file}[/green]")
    else:
        console.print("[yellow]⚠️  Learning mode not configured[/yellow]")


if __name__ == '__main__':
    learning_cli()


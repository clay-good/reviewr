"""
CLI commands for reviewr web dashboard.

This module provides commands to start and manage the reviewr web dashboard.
"""

import click
import sys
from pathlib import Path


@click.group('dashboard')
def dashboard():
    """Manage the reviewr web dashboard."""
    pass


@dashboard.command('start')
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
@click.option('--database-url', default='sqlite:///reviewr.db', help='Database URL')
def start_dashboard(host: str, port: int, reload: bool, database_url: str):
    """
    Start the reviewr web dashboard server.
    
    Examples:
        reviewr dashboard start
        reviewr dashboard start --port 8080
        reviewr dashboard start --reload  # Development mode
    """
    try:
        import uvicorn
    except ImportError:
        click.echo("❌ Error: uvicorn is not installed", err=True)
        click.echo("Install it with: pip install uvicorn", err=True)
        sys.exit(1)
    
    try:
        from reviewr.dashboard.api import app
        from reviewr.dashboard.database import DatabaseManager
    except ImportError as e:
        click.echo(f"❌ Error: Failed to import dashboard modules: {e}", err=True)
        click.echo("Make sure all dependencies are installed: pip install fastapi sqlalchemy", err=True)
        sys.exit(1)
    
    # Initialize database
    click.echo("🔧 Initializing database...")
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    click.echo("✅ Database initialized")
    
    # Start server
    click.echo(f"\n🚀 Starting reviewr dashboard...")
    click.echo(f"   Host: {host}")
    click.echo(f"   Port: {port}")
    click.echo(f"   Database: {database_url}")
    click.echo(f"\n📊 Dashboard URL: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    click.echo(f"📖 API Docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    click.echo("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "reviewr.dashboard.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


@dashboard.command('init-db')
@click.option('--database-url', default='sqlite:///reviewr.db', help='Database URL')
@click.option('--drop', is_flag=True, help='Drop existing tables first')
def init_database(database_url: str, drop: bool):
    """
    Initialize the dashboard database.
    
    Examples:
        reviewr dashboard init-db
        reviewr dashboard init-db --drop  # Drop and recreate tables
    """
    try:
        from reviewr.dashboard.database import DatabaseManager
    except ImportError as e:
        click.echo(f"❌ Error: Failed to import database module: {e}", err=True)
        sys.exit(1)
    
    db_manager = DatabaseManager(database_url)
    
    if drop:
        click.echo("⚠️  Dropping existing tables...")
        db_manager.drop_tables()
        click.echo("✅ Tables dropped")
    
    click.echo("🔧 Creating database tables...")
    db_manager.create_tables()
    click.echo("✅ Database initialized successfully")
    click.echo(f"   Database: {database_url}")


@dashboard.command('add-project')
@click.argument('name')
@click.option('--repository-url', help='Repository URL')
@click.option('--description', help='Project description')
@click.option('--language', help='Primary programming language')
@click.option('--database-url', default='sqlite:///reviewr.db', help='Database URL')
def add_project(name: str, repository_url: str, description: str, language: str, database_url: str):
    """
    Add a new project to the dashboard.
    
    Examples:
        reviewr dashboard add-project my-app
        reviewr dashboard add-project my-app --language python --repository-url https://github.com/user/repo
    """
    try:
        from reviewr.dashboard.database import DatabaseManager, Project
    except ImportError as e:
        click.echo(f"❌ Error: Failed to import database module: {e}", err=True)
        sys.exit(1)
    
    db_manager = DatabaseManager(database_url)
    session = db_manager.get_session()
    
    try:
        # Check if project exists
        existing = session.query(Project).filter_by(name=name).first()
        if existing:
            click.echo(f"❌ Error: Project '{name}' already exists", err=True)
            sys.exit(1)
        
        # Create project
        project = Project(
            name=name,
            repository_url=repository_url,
            description=description,
            language=language
        )
        session.add(project)
        session.commit()
        
        click.echo(f"✅ Project '{name}' added successfully")
        click.echo(f"   ID: {project.id}")
        if repository_url:
            click.echo(f"   Repository: {repository_url}")
        if language:
            click.echo(f"   Language: {language}")
    
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@dashboard.command('list-projects')
@click.option('--database-url', default='sqlite:///reviewr.db', help='Database URL')
def list_projects(database_url: str):
    """
    List all projects in the dashboard.
    
    Examples:
        reviewr dashboard list-projects
    """
    try:
        from reviewr.dashboard.database import DatabaseManager, Project
    except ImportError as e:
        click.echo(f"❌ Error: Failed to import database module: {e}", err=True)
        sys.exit(1)
    
    db_manager = DatabaseManager(database_url)
    session = db_manager.get_session()
    
    try:
        projects = session.query(Project).all()
        
        if not projects:
            click.echo("No projects found")
            return
        
        click.echo(f"\n📊 Projects ({len(projects)}):\n")
        
        for project in projects:
            click.echo(f"  • {project.name} (ID: {project.id})")
            if project.language:
                click.echo(f"    Language: {project.language}")
            if project.repository_url:
                click.echo(f"    Repository: {project.repository_url}")
            click.echo(f"    Created: {project.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo()
    
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@dashboard.command('stats')
@click.option('--database-url', default='sqlite:///reviewr.db', help='Database URL')
def show_stats(database_url: str):
    """
    Show dashboard statistics.

    Examples:
        reviewr dashboard stats
    """
    try:
        from reviewr.dashboard.database import DatabaseManager, Project, Review, Finding
        from sqlalchemy import func
    except ImportError as e:
        click.echo(f"❌ Error: Failed to import database module: {e}", err=True)
        sys.exit(1)

    db_manager = DatabaseManager(database_url)
    session = db_manager.get_session()

    try:
        # Get counts
        total_projects = session.query(func.count(Project.id)).scalar()
        total_reviews = session.query(func.count(Review.id)).scalar()
        total_findings = session.query(func.count(Finding.id)).scalar()

        # Get severity counts
        critical = session.query(func.sum(Review.critical_findings)).scalar() or 0
        high = session.query(func.sum(Review.high_findings)).scalar() or 0
        medium = session.query(func.sum(Review.medium_findings)).scalar() or 0
        low = session.query(func.sum(Review.low_findings)).scalar() or 0

        click.echo("\n📊 Dashboard Statistics\n")
        click.echo(f"  Projects:  {total_projects}")
        click.echo(f"  Reviews:   {total_reviews}")
        click.echo(f"  Findings:  {total_findings}")
        click.echo("\n  Severity Breakdown:")
        click.echo(f"    Critical: {critical}")
        click.echo(f"    High:     {high}")
        click.echo(f"    Medium:   {medium}")
        click.echo(f"    Low:      {low}")
        click.echo()

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    finally:
        session.close()


@dashboard.command('upload')
@click.argument('results_file', type=click.Path(exists=True))
@click.option('--project-name', required=True, help='Project name')
@click.option('--commit-sha', help='Commit SHA')
@click.option('--branch', help='Branch name')
@click.option('--author', help='Author name')
@click.option('--database-url', default='sqlite:///reviewr.db', help='Database URL')
def upload_results(results_file: str, project_name: str, commit_sha: str, branch: str, author: str, database_url: str):
    """
    Upload review results to the dashboard.

    Examples:
        reviewr dashboard upload results.json --project-name my-app
        reviewr dashboard upload results.json --project-name my-app --commit-sha abc123 --branch main
    """
    import json
    from datetime import datetime

    try:
        from reviewr.dashboard.database import DatabaseManager, Project, Review, Finding
    except ImportError as e:
        click.echo(f"❌ Error: Failed to import database module: {e}", err=True)
        sys.exit(1)

    # Load results file
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
    except Exception as e:
        click.echo(f"❌ Error: Failed to load results file: {e}", err=True)
        sys.exit(1)

    db_manager = DatabaseManager(database_url)
    session = db_manager.get_session()

    try:
        # Get or create project
        project = session.query(Project).filter_by(name=project_name).first()
        if not project:
            click.echo(f"📦 Creating project '{project_name}'...")
            project = Project(name=project_name)
            session.add(project)
            session.flush()

        # Create review
        click.echo(f"📊 Creating review record...")
        review = Review(
            project_id=project.id,
            commit_sha=commit_sha,
            branch=branch,
            author=author,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            status='completed'
        )

        # Extract metadata from results
        if 'metadata' in results:
            metadata = results['metadata']
            review.files_reviewed = metadata.get('total_files', 0)
            review.lines_reviewed = metadata.get('total_lines', 0)
            review.provider = metadata.get('provider')
            review.model = metadata.get('model')
            review.total_tokens = metadata.get('total_tokens')
            review.total_cost = metadata.get('total_cost')
            review.duration_seconds = metadata.get('duration_seconds')

        session.add(review)
        session.flush()

        # Add findings
        findings = results.get('findings', [])
        click.echo(f"📝 Adding {len(findings)} findings...")

        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}

        for finding_data in findings:
            finding = Finding(
                review_id=review.id,
                type=finding_data.get('type', 'unknown'),
                severity=finding_data.get('severity', 'info'),
                category=finding_data.get('category'),
                file_path=finding_data.get('file', ''),
                line_start=finding_data.get('line', 0),
                line_end=finding_data.get('line_end', finding_data.get('line', 0)),
                message=finding_data.get('message', ''),
                suggestion=finding_data.get('suggestion'),
                code_snippet=finding_data.get('code_snippet'),
                confidence=finding_data.get('confidence'),
                status='open'
            )
            session.add(finding)

            # Count by severity
            severity = finding_data.get('severity', 'info').lower()
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Update review statistics
        review.total_findings = len(findings)
        review.critical_findings = severity_counts['critical']
        review.high_findings = severity_counts['high']
        review.medium_findings = severity_counts['medium']
        review.low_findings = severity_counts['low']
        review.info_findings = severity_counts['info']

        session.commit()

        click.echo(f"\n✅ Review uploaded successfully!")
        click.echo(f"   Project: {project_name}")
        click.echo(f"   Review ID: {review.id}")
        click.echo(f"   Total Findings: {review.total_findings}")
        click.echo(f"     Critical: {review.critical_findings}")
        click.echo(f"     High: {review.high_findings}")
        click.echo(f"     Medium: {review.medium_findings}")
        click.echo(f"     Low: {review.low_findings}")
        click.echo(f"     Info: {review.info_findings}")
        click.echo()

    except Exception as e:
        session.rollback()
        click.echo(f"❌ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


# Alias for import in main CLI
dashboard_cli = dashboard


if __name__ == '__main__':
    dashboard()


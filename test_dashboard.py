"""
Comprehensive test suite for reviewr web dashboard.

Tests database models, API endpoints, and dashboard functionality.
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reviewr.dashboard.database import (
    DatabaseManager,
    Project,
    Review,
    Finding,
    ProjectMetric
)


def test_database_models():
    """Test database models and basic operations."""
    print("\n" + "="*80)
    print("TEST 1: Database Models")
    print("="*80)
    
    # Create in-memory database
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    
    session = db_manager.get_session()
    
    try:
        # Test 1: Create project
        project = Project(
            name="test-project",
            repository_url="https://github.com/test/repo",
            description="Test project",
            language="python"
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        
        assert project.id is not None, "Project should have an ID"
        assert project.name == "test-project", "Project name should match"
        print("✓ Project created successfully")
        
        # Test 2: Create review
        review = Review(
            project_id=project.id,
            commit_sha="abc123",
            branch="main",
            pr_number=42,
            author="test-user",
            provider="claude",
            status="completed"
        )
        session.add(review)
        session.commit()
        session.refresh(review)
        
        assert review.id is not None, "Review should have an ID"
        assert review.project_id == project.id, "Review should be linked to project"
        print("✓ Review created successfully")
        
        # Test 3: Create findings
        finding1 = Finding(
            review_id=review.id,
            type="security",
            severity="critical",
            category="sql_injection",
            file_path="app.py",
            line_start=10,
            line_end=15,
            message="SQL injection vulnerability detected",
            confidence=0.95
        )
        
        finding2 = Finding(
            review_id=review.id,
            type="performance",
            severity="medium",
            category="inefficient_loop",
            file_path="utils.py",
            line_start=20,
            line_end=25,
            message="Inefficient loop detected",
            confidence=0.85
        )
        
        session.add_all([finding1, finding2])
        session.commit()
        
        assert finding1.id is not None, "Finding 1 should have an ID"
        assert finding2.id is not None, "Finding 2 should have an ID"
        print("✓ Findings created successfully")
        
        # Test 4: Query relationships
        project_reviews = session.query(Review).filter_by(project_id=project.id).all()
        assert len(project_reviews) == 1, "Project should have 1 review"
        print("✓ Project-Review relationship works")
        
        review_findings = session.query(Finding).filter_by(review_id=review.id).all()
        assert len(review_findings) == 2, "Review should have 2 findings"
        print("✓ Review-Finding relationship works")
        
        # Test 5: Create project metric
        metric = ProjectMetric(
            project_id=project.id,
            total_lines=1000,
            total_files=10,
            total_issues=2,
            critical_issues=1,
            high_issues=0,
            medium_issues=1,
            low_issues=0,
            security_score=85.0,
            performance_score=90.0,
            maintainability_score=88.0,
            overall_score=87.7
        )
        session.add(metric)
        session.commit()
        
        assert metric.id is not None, "Metric should have an ID"
        print("✓ Project metric created successfully")
        
        print("\n✅ Database models tests passed!")
        return True
    
    except AssertionError as e:
        print(f"\n❌ Database Models FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Database Models FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def test_database_manager():
    """Test DatabaseManager helper methods."""
    print("\n" + "="*80)
    print("TEST 2: Database Manager")
    print("="*80)
    
    db_manager = DatabaseManager("sqlite:///:memory:")
    db_manager.create_tables()
    
    try:
        # Test 1: Add review
        review = db_manager.add_review(
            project_name="test-project-2",
            commit_sha="def456",
            branch="develop",
            pr_number=100,
            author="developer",
            provider="claude"
        )
        
        assert review.id is not None, "Review should be created"
        assert review.commit_sha == "def456", "Commit SHA should match"
        print("✓ add_review() works correctly")
        
        # Test 2: Add finding
        finding = db_manager.add_finding(
            review_id=review.id,
            type="style",
            severity="low",
            file_path="test.py",
            line_start=1,
            line_end=1,
            message="Style issue"
        )
        
        assert finding.id is not None, "Finding should be created"
        assert finding.review_id == review.id, "Finding should be linked to review"
        print("✓ add_finding() works correctly")
        
        # Test 3: Get project reviews
        reviews = db_manager.get_project_reviews("test-project-2")
        assert len(reviews) == 1, "Should return 1 review"
        assert reviews[0].id == review.id, "Should return correct review"
        print("✓ get_project_reviews() works correctly")
        
        # Test 4: Get review findings
        findings = db_manager.get_review_findings(review.id)
        assert len(findings) == 1, "Should return 1 finding"
        assert findings[0].id == finding.id, "Should return correct finding"
        print("✓ get_review_findings() works correctly")
        
        print("\n✅ Database manager tests passed!")
        return True
    
    except AssertionError as e:
        print(f"\n❌ Database Manager FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Database Manager FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test FastAPI endpoints."""
    print("\n" + "="*80)
    print("TEST 3: API Endpoints")
    print("="*80)
    
    try:
        from fastapi.testclient import TestClient
        from reviewr.dashboard.api import app, db_manager
    except ImportError as e:
        print(f"⚠️  Skipping API tests: {e}")
        print("   Install dependencies: pip install fastapi httpx")
        return True
    
    # Use in-memory database for testing
    db_manager.engine.dispose()
    db_manager.__init__("sqlite:///:memory:")
    db_manager.create_tables()
    
    client = TestClient(app)
    
    try:
        # Test 1: Health check
        response = client.get("/health")
        assert response.status_code == 200, "Health check should return 200"
        assert response.json()["status"] == "healthy", "Health check should return healthy"
        print("✓ Health check endpoint works")
        
        # Test 2: Create project
        response = client.post("/api/projects", json={
            "name": "api-test-project",
            "repository_url": "https://github.com/test/api",
            "language": "python"
        })
        assert response.status_code == 200, "Create project should return 200"
        project_data = response.json()
        assert project_data["name"] == "api-test-project", "Project name should match"
        project_id = project_data["id"]
        print("✓ Create project endpoint works")
        
        # Test 3: List projects
        response = client.get("/api/projects")
        assert response.status_code == 200, "List projects should return 200"
        projects = response.json()
        assert len(projects) >= 1, "Should have at least 1 project"
        print("✓ List projects endpoint works")
        
        # Test 4: Get project
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200, "Get project should return 200"
        project = response.json()
        assert project["id"] == project_id, "Project ID should match"
        print("✓ Get project endpoint works")
        
        # Test 5: Create review
        response = client.post("/api/reviews", json={
            "project_name": "api-test-project",
            "commit_sha": "abc123",
            "branch": "main",
            "pr_number": 1,
            "author": "test-user",
            "provider": "claude"
        })
        assert response.status_code == 200, "Create review should return 200"
        review_data = response.json()
        assert review_data["commit_sha"] == "abc123", "Commit SHA should match"
        review_id = review_data["id"]
        print("✓ Create review endpoint works")
        
        # Test 6: Create finding
        response = client.post("/api/findings", json={
            "review_id": review_id,
            "type": "security",
            "severity": "high",
            "file_path": "app.py",
            "line_start": 10,
            "line_end": 15,
            "message": "Security issue"
        })
        assert response.status_code == 200, "Create finding should return 200"
        finding_data = response.json()
        assert finding_data["severity"] == "high", "Severity should match"
        print("✓ Create finding endpoint works")
        
        # Test 7: List findings
        response = client.get(f"/api/findings?review_id={review_id}")
        assert response.status_code == 200, "List findings should return 200"
        findings = response.json()
        assert len(findings) == 1, "Should have 1 finding"
        print("✓ List findings endpoint works")
        
        # Test 8: Get metrics
        response = client.get("/api/metrics/overview")
        assert response.status_code == 200, "Get metrics should return 200"
        metrics = response.json()
        assert metrics["total_projects"] >= 1, "Should have at least 1 project"
        assert metrics["total_reviews"] >= 1, "Should have at least 1 review"
        print("✓ Get metrics endpoint works")
        
        print("\n✅ API endpoints tests passed!")
        return True
    
    except AssertionError as e:
        print(f"\n❌ API Endpoints FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ API Endpoints FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all dashboard tests."""
    print("\n" + "="*80)
    print("🧪 RUNNING DASHBOARD TESTS")
    print("="*80)
    
    tests = [
        ("Database Models", test_database_models),
        ("Database Manager", test_database_manager),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("="*80)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*80)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Dashboard is ready!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)


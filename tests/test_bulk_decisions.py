"""
Comprehensive tests for bulk decision operations.
Tests bulk create and update endpoints with various scenarios including
success cases, validation failures, partial failures, and edge cases.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app import models, schemas_bulk
from tests.conftest import TestingSessionLocal, override_get_db, engine

client = TestClient(app)

class TestBulkDecisionCreate:
    """Test cases for bulk decision creation endpoint."""

    def setup_method(self):
        """Set up test data before each test."""
        models.Base.metadata.create_all(bind=engine)
        
        # Create test project
        with TestingSessionLocal() as db:
            test_project = models.Project(
                name="test-project",
                path="/test/path",
                description="Test project for bulk operations"
            )
            db.add(test_project)
            db.commit()
            db.refresh(test_project)
            self.project_id = test_project.id
            
            # Create test task for decision association
            test_task = models.Task(
                title="Test Task",
                description="Task for decision association",
                project_id=self.project_id
            )
            db.add(test_task)
            db.commit()
            db.refresh(test_task)
            self.task_id = test_task.id

    def teardown_method(self):
        """Clean up after each test."""
        models.Base.metadata.drop_all(bind=engine)

    def test_bulk_create_decisions_success(self):
        """Test successful bulk decision creation."""
        bulk_request = {
            "decisions": [
                {
                    "title": "Decision 1",
                    "context_md": "## Context\nThis is the first decision context",
                    "decision_md": "## Decision\nWe decided to use approach A",
                    "consequences_md": "## Consequences\nThis will improve performance",
                    "task_id": self.task_id
                },
                {
                    "title": "Decision 2",
                    "context_md": "## Context\nSecond decision context",
                    "decision_md": "## Decision\nWe decided to use approach B"
                },
                {
                    "title": "Decision 3"
                    # Minimal decision with just title
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 3
        assert data["total_successful"] == 3
        assert data["total_failed"] == 0
        assert data["operation_type"] == "create"
        assert len(data["successful_decisions"]) == 3
        assert len(data["failed_items"]) == 0
        
        # Verify decision details
        decisions = data["successful_decisions"]
        assert decisions[0]["title"] == "Decision 1"
        assert decisions[0]["task_id"] == self.task_id
        assert "approach A" in decisions[0]["decision_md"]
        assert decisions[1]["title"] == "Decision 2"
        assert decisions[1]["task_id"] is None
        assert decisions[2]["title"] == "Decision 3"

    def test_bulk_create_decisions_with_invalid_task(self):
        """Test bulk decision creation with invalid task ID."""
        bulk_request = {
            "decisions": [
                {
                    "title": "Valid Decision",
                    "context_md": "This should succeed"
                },
                {
                    "title": "Invalid Task Decision",
                    "context_md": "This should fail",
                    "task_id": 99999  # Non-existent task
                },
                {
                    "title": "Another Valid Decision",
                    "context_md": "This should also succeed"
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 3
        assert data["total_successful"] == 2
        assert data["total_failed"] == 1
        
        # Check successful decisions
        assert len(data["successful_decisions"]) == 2
        assert data["successful_decisions"][0]["title"] == "Valid Decision"
        assert data["successful_decisions"][1]["title"] == "Another Valid Decision"
        
        # Check failed item
        assert len(data["failed_items"]) == 1
        failed_item = data["failed_items"][0]
        assert failed_item["index"] == 1
        assert failed_item["error_code"] == "TASK_NOT_FOUND"
        assert "Task with ID 99999 not found" in failed_item["error_message"]

    def test_bulk_create_decisions_empty_list(self):
        """Test bulk decision creation with empty decision list."""
        bulk_request = {"decisions": []}
        
        response = client.post(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 0
        assert data["total_successful"] == 0
        assert data["total_failed"] == 0
        assert len(data["successful_decisions"]) == 0
        assert len(data["failed_items"]) == 0

    def test_bulk_create_decisions_missing_title(self):
        """Test bulk decision creation with missing required title."""
        bulk_request = {
            "decisions": [
                {
                    "context_md": "Decision without title"
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        # Should return 422 for validation error
        assert response.status_code == 422

    def test_bulk_create_decisions_nonexistent_project(self):
        """Test bulk decision creation with non-existent project."""
        bulk_request = {
            "decisions": [
                {
                    "title": "Test Decision",
                    "context_md": "This should fail"
                }
            ]
        }
        
        response = client.post("/99999/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 404

    def test_bulk_create_decisions_markdown_content(self):
        """Test bulk decision creation with rich markdown content."""
        bulk_request = {
            "decisions": [
                {
                    "title": "Architecture Decision",
                    "context_md": """
# Context

We need to choose between two architectural approaches:

1. **Microservices**: Better scalability but more complexity
2. **Monolith**: Simpler deployment but potential scaling issues

## Current State
- Team size: 5 developers
- Expected load: 1000 requests/day
                    """,
                    "decision_md": """
# Decision

We decided to start with a **monolithic architecture** for the following reasons:

- Small team size makes microservices overhead significant
- Current load doesn't justify microservices complexity
- Faster time to market
                    """,
                    "consequences_md": """
# Consequences

## Positive
- Faster development cycle
- Easier debugging and testing
- Simpler deployment process

## Negative  
- May need to refactor later if we scale
- All components share the same technology stack
                    """
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_successful"] == 1
        decision = data["successful_decisions"][0]
        assert "Microservices" in decision["context_md"]
        assert "monolithic architecture" in decision["decision_md"]
        assert "Positive" in decision["consequences_md"]


class TestBulkDecisionUpdate:
    """Test cases for bulk decision update endpoint."""

    def setup_method(self):
        """Set up test data before each test."""
        models.Base.metadata.create_all(bind=engine)
        
        # Create test project
        with TestingSessionLocal() as db:
            test_project = models.Project(
                name="test-project",
                path="/test/path",
                description="Test project for bulk operations"
            )
            db.add(test_project)
            db.commit()
            db.refresh(test_project)
            self.project_id = test_project.id
            
            # Create test task
            test_task = models.Task(
                title="Test Task",
                description="Task for decision association",
                project_id=self.project_id
            )
            db.add(test_task)
            db.commit()
            db.refresh(test_task)
            self.task_id = test_task.id
            
            # Create test decisions - store IDs only to avoid detached objects
            self.decision_ids = []
            for i in range(3):
                decision = models.Decision(
                    title=f"Decision {i+1}",
                    context_md=f"Context for decision {i+1}",
                    decision_md=f"Decision content {i+1}",
                    project_id=self.project_id,
                    status=models.DecisionStatus.PROPOSED
                )
                db.add(decision)
                db.commit()
                db.refresh(decision)
                self.decision_ids.append(decision.id)

    def teardown_method(self):
        """Clean up after each test."""
        models.Base.metadata.drop_all(bind=engine)

    def test_bulk_update_decisions_success(self):
        """Test successful bulk decision update."""
        bulk_request = {
            "updates": [
                {
                    "id": self.decision_ids[0],
                    "update": {
                        "title": "Updated Decision 1",
                        "status": "Accepted"
                    }
                },
                {
                    "id": self.decision_ids[1],
                    "update": {
                        "context_md": "Updated context with more details",
                        "decision_md": "Updated decision rationale"
                    }
                },
                {
                    "id": self.decision_ids[2],
                    "update": {
                        "status": "Rejected",
                        "consequences_md": "Updated consequences analysis"
                    }
                }
            ]
        }
        
        response = client.put(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 3
        assert data["total_successful"] == 3
        assert data["total_failed"] == 0
        assert data["operation_type"] == "update"
        
        # Verify updates
        decisions = data["successful_decisions"]
        decision_by_id = {decision["id"]: decision for decision in decisions}
        
        # Check first decision
        decision1 = decision_by_id[self.decision_ids[0]]
        assert decision1["title"] == "Updated Decision 1"
        assert decision1["status"] == "Accepted"
        
        # Check second decision
        decision2 = decision_by_id[self.decision_ids[1]]
        assert "more details" in decision2["context_md"]
        assert "Updated decision rationale" in decision2["decision_md"]
        
        # Check third decision
        decision3 = decision_by_id[self.decision_ids[2]]
        assert decision3["status"] == "Rejected"
        assert "Updated consequences" in decision3["consequences_md"]

    def test_bulk_update_decisions_status_changes(self):
        """Test bulk decision updates with status changes."""
        bulk_request = {
            "updates": [
                {
                    "id": self.decision_ids[0],
                    "update": {
                        "status": "Accepted"
                    }
                },
                {
                    "id": self.decision_ids[1],
                    "update": {
                        "status": "Rejected"
                    }
                }
            ]
        }
        
        response = client.put(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        decisions = data["successful_decisions"]
        
        # Verify status changes
        assert decisions[0]["status"] == "Accepted"
        assert decisions[1]["status"] == "Rejected"

    def test_bulk_update_decisions_nonexistent_decision(self):
        """Test bulk update with non-existent decision ID."""
        bulk_request = {
            "updates": [
                {
                    "id": self.decision_ids[0],
                    "update": {
                        "title": "Valid Update"
                    }
                },
                {
                    "id": 99999,  # Non-existent decision
                    "update": {
                        "title": "Invalid Update"
                    }
                }
            ]
        }
        
        response = client.put(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 2
        assert data["total_successful"] == 1
        assert data["total_failed"] == 1
        
        # Check successful update
        assert len(data["successful_decisions"]) == 1
        assert data["successful_decisions"][0]["title"] == "Valid Update"
        
        # Check failed update
        assert len(data["failed_items"]) == 1
        failed_item = data["failed_items"][0]
        assert failed_item["item_id"] == 99999
        assert failed_item["error_code"] == "DECISION_NOT_FOUND"

    def test_bulk_update_decisions_empty_updates(self):
        """Test bulk update with empty updates list."""
        bulk_request = {"updates": []}
        
        response = client.put(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 0
        assert data["total_successful"] == 0
        assert data["total_failed"] == 0

    def test_bulk_update_decisions_partial_update(self):
        """Test bulk update with partial field updates."""
        bulk_request = {
            "updates": [
                {
                    "id": self.decision_ids[0],
                    "update": {
                        "title": "Only Title Updated"
                        # Don't update context_md, decision_md, etc.
                    }
                }
            ]
        }
        
        response = client.put(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        updated_decision = data["successful_decisions"][0]
        
        # Title should be updated
        assert updated_decision["title"] == "Only Title Updated"
        
        # Other fields should remain unchanged - verify with expected original values
        assert updated_decision["context_md"] == "Context for decision 1"
        assert updated_decision["decision_md"] == "Decision content 1"
        assert updated_decision["status"] == "Proposed"


class TestBulkDecisionEdgeCases:
    """Test edge cases and error scenarios for bulk decision operations."""

    def setup_method(self):
        """Set up test data before each test."""
        models.Base.metadata.create_all(bind=engine)
        
        with TestingSessionLocal() as db:
            test_project = models.Project(
                name="test-project",
                path="/test/path",
                description="Test project for bulk operations"
            )
            db.add(test_project)
            db.commit()
            db.refresh(test_project)
            self.project_id = test_project.id

    def teardown_method(self):
        """Clean up after each test."""
        models.Base.metadata.drop_all(bind=engine)

    def test_bulk_create_decisions_large_batch(self):
        """Test bulk creation with a large number of decisions."""
        decisions = [
            {
                "title": f"Decision {i}",
                "context_md": f"Context {i}",
                "decision_md": f"Decision content {i}"
            }
            for i in range(50)
        ]
        bulk_request = {"decisions": decisions}
        
        response = client.post(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 50
        assert data["total_successful"] == 50
        assert data["total_failed"] == 0

    def test_bulk_decisions_malformed_request(self):
        """Test bulk operations with malformed request data."""
        # Missing required 'decisions' field
        response = client.post(f"/{self.project_id}/decisions/bulk", json={})
        assert response.status_code == 422
        
        # Invalid data type for decisions
        response = client.post(f"/{self.project_id}/decisions/bulk", json={"decisions": "invalid"})
        assert response.status_code == 422

    def test_bulk_decisions_unicode_content(self):
        """Test bulk operations with unicode content."""
        bulk_request = {
            "decisions": [
                {
                    "title": "Unicode Decision: 决定 🎯",
                    "context_md": "# Context with unicode: 背景 📋\n\nSome **unicode** content with émojis 🚀",
                    "decision_md": "# Decision: 決定事項 ✅\n\nUnicode decision content: ñáéíóú"
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_successful"] == 1
        decision = data["successful_decisions"][0]
        assert "决定 🎯" in decision["title"]
        assert "背景 📋" in decision["context_md"]
        assert "決定事項 ✅" in decision["decision_md"]

    def test_bulk_decisions_very_long_markdown(self):
        """Test bulk operations with very long markdown content."""
        long_context = "# Context\n\n" + "This is a very long context. " * 200
        long_decision = "# Decision\n\n" + "This is a very long decision. " * 200
        long_consequences = "# Consequences\n\n" + "These are very long consequences. " * 200
        
        bulk_request = {
            "decisions": [
                {
                    "title": "Long Content Decision",
                    "context_md": long_context,
                    "decision_md": long_decision,
                    "consequences_md": long_consequences
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        # Should succeed (assuming no length limits in schema)
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_successful"] == 1
        decision = data["successful_decisions"][0]
        assert len(decision["context_md"]) > 1000
        assert len(decision["decision_md"]) > 1000
        assert len(decision["consequences_md"]) > 1000

    def test_bulk_decisions_complex_markdown(self):
        """Test bulk operations with complex markdown formatting."""
        complex_markdown = """
# Architecture Decision Record

## Status
**Proposed** → *Under Review*

## Context
We need to decide between:

| Option | Pros | Cons |
|--------|------|------|
| Redis | Fast | Memory intensive |
| PostgreSQL | ACID | Slower |

### Code Example
```python
def cache_data(key, value):
    redis_client.set(key, value, ex=3600)
```

## Decision
After careful consideration, we choose **Redis** for the following reasons:

1. Performance requirements
2. Existing team expertise
3. Infrastructure compatibility

> **Note**: This decision will be reviewed in Q2 2024

## Consequences

### ✅ Positive
- Improved response times
- Better user experience

### ❌ Negative  
- Higher memory usage
- Additional infrastructure complexity

---
*Decision made on 2024-01-15*
        """
        
        bulk_request = {
            "decisions": [
                {
                    "title": "Cache Technology Selection",
                    "context_md": complex_markdown,
                    "decision_md": "We decided to use Redis as our primary caching solution.",
                    "consequences_md": complex_markdown
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_successful"] == 1
        decision = data["successful_decisions"][0]
        assert "Redis" in decision["context_md"]
        assert "```python" in decision["context_md"]
        assert "| Option |" in decision["context_md"]
        assert "Decision made on 2024-01-15" in decision["consequences_md"]

    def test_bulk_decisions_all_status_values(self):
        """Test bulk operations with all possible decision status values."""
        statuses = ["Proposed", "Accepted", "Rejected", "Superseded"]
        
        # Create decisions for updating
        decision_ids = []
        with TestingSessionLocal() as db:
            for i, status in enumerate(statuses):
                decision = models.Decision(
                    title=f"Decision {i+1}",
                    context_md=f"Context {i+1}",
                    project_id=self.project_id,
                    status=models.DecisionStatus.PROPOSED
                )
                db.add(decision)
                db.commit()
                db.refresh(decision)
                decision_ids.append(decision.id)
        
        # Update decisions to different statuses
        bulk_request = {
            "updates": [
                {
                    "id": decision_ids[i],
                    "update": {
                        "status": status
                    }
                }
                for i, status in enumerate(statuses)
            ]
        }
        
        response = client.put(f"/{self.project_id}/decisions/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_successful"] == 4
        
        # Verify all status values are correctly set
        decisions_result = data["successful_decisions"]
        result_statuses = [d["status"] for d in decisions_result]
        assert set(result_statuses) == set(statuses)

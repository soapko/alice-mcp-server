"""
Comprehensive tests for bulk task operations.
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

class TestBulkTaskCreate:
    """Test cases for bulk task creation endpoint."""

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
            
            # Create test epic
            test_epic = models.Epic(
                title="Test Epic",
                description="Test epic for bulk operations",
                project_id=self.project_id
            )
            db.add(test_epic)
            db.commit()
            db.refresh(test_epic)
            self.epic_id = test_epic.id

    def teardown_method(self):
        """Clean up after each test."""
        models.Base.metadata.drop_all(bind=engine)

    def test_bulk_create_tasks_success(self):
        """Test successful bulk task creation."""
        bulk_request = {
            "tasks": [
                {
                    "title": "Task 1",
                    "description": "First test task",
                    "status": "To-Do",
                    "epic_id": self.epic_id
                },
                {
                    "title": "Task 2",
                    "description": "Second test task",
                    "status": "In Progress"
                },
                {
                    "title": "Task 3",
                    "description": "Third test task"
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 3
        assert data["total_successful"] == 3
        assert data["total_failed"] == 0
        assert data["operation_type"] == "create"
        assert len(data["successful_tasks"]) == 3
        assert len(data["failed_items"]) == 0
        
        # Verify task details
        tasks = data["successful_tasks"]
        assert tasks[0]["title"] == "Task 1"
        assert tasks[0]["epic_id"] == self.epic_id
        assert tasks[1]["title"] == "Task 2"
        assert tasks[1]["status"] == "In Progress"
        assert tasks[2]["title"] == "Task 3"
        assert tasks[2]["status"] == "To-Do"  # Default status

    def test_bulk_create_tasks_with_invalid_epic(self):
        """Test bulk task creation with invalid epic ID."""
        bulk_request = {
            "tasks": [
                {
                    "title": "Valid Task",
                    "description": "This should succeed"
                },
                {
                    "title": "Invalid Epic Task",
                    "description": "This should fail",
                    "epic_id": 99999  # Non-existent epic
                },
                {
                    "title": "Another Valid Task",
                    "description": "This should also succeed"
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 3
        assert data["total_successful"] == 2
        assert data["total_failed"] == 1
        
        # Check successful tasks
        assert len(data["successful_tasks"]) == 2
        assert data["successful_tasks"][0]["title"] == "Valid Task"
        assert data["successful_tasks"][1]["title"] == "Another Valid Task"
        
        # Check failed item
        assert len(data["failed_items"]) == 1
        failed_item = data["failed_items"][0]
        assert failed_item["index"] == 1
        assert failed_item["error_code"] == "EPIC_NOT_FOUND"
        assert "Epic with ID 99999 not found" in failed_item["error_message"]

    def test_bulk_create_tasks_empty_list(self):
        """Test bulk task creation with empty task list."""
        bulk_request = {"tasks": []}
        
        response = client.post(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 0
        assert data["total_successful"] == 0
        assert data["total_failed"] == 0
        assert len(data["successful_tasks"]) == 0
        assert len(data["failed_items"]) == 0

    def test_bulk_create_tasks_missing_title(self):
        """Test bulk task creation with missing required title."""
        bulk_request = {
            "tasks": [
                {
                    "description": "Task without title"
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        # Should return 422 for validation error
        assert response.status_code == 422

    def test_bulk_create_tasks_nonexistent_project(self):
        """Test bulk task creation with non-existent project."""
        bulk_request = {
            "tasks": [
                {
                    "title": "Test Task",
                    "description": "This should fail"
                }
            ]
        }
        
        response = client.post("/99999/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 404

    def test_bulk_create_tasks_with_status_history(self):
        """Test that status history is created for non-default statuses."""
        bulk_request = {
            "tasks": [
                {
                    "title": "In Progress Task",
                    "status": "In Progress"
                },
                {
                    "title": "Todo Task",
                    "status": "To-Do"
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        tasks = data["successful_tasks"]
        
        # First task should have status history (non-default status)
        assert len(tasks[0]["status_history"]) == 1
        assert tasks[0]["status_history"][0]["new_status"] == "In Progress"
        
        # Second task should have no status history (default status, no history created)
        assert len(tasks[1]["status_history"]) == 0


class TestBulkTaskUpdate:
    """Test cases for bulk task update endpoint."""

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
            
            # Create test epic
            test_epic = models.Epic(
                title="Test Epic",
                description="Test epic for bulk operations",
                project_id=self.project_id
            )
            db.add(test_epic)
            db.commit()
            db.refresh(test_epic)
            self.epic_id = test_epic.id
            
            # Create test tasks
            self.task_ids = []
            for i in range(3):
                task = models.Task(
                    title=f"Task {i+1}",
                    description=f"Test task {i+1}",
                    project_id=self.project_id,
                    status=models.TaskStatus.TODO
                )
                db.add(task)
                db.commit()
                db.refresh(task)
                self.task_ids.append(task.id)

    def teardown_method(self):
        """Clean up after each test."""
        models.Base.metadata.drop_all(bind=engine)

    def test_bulk_update_tasks_success(self):
        """Test successful bulk task update."""
        bulk_request = {
            "updates": [
                {
                    "id": self.task_ids[0],
                    "update": {
                        "title": "Updated Task 1",
                        "status": "In Progress"
                    }
                },
                {
                    "id": self.task_ids[1],
                    "update": {
                        "description": "Updated description",
                        "epic_id": self.epic_id
                    }
                },
                {
                    "id": self.task_ids[2],
                    "update": {
                        "status": "Done",
                        "assignee": "test-user"
                    }
                }
            ]
        }
        
        response = client.put(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 3
        assert data["total_successful"] == 3
        assert data["total_failed"] == 0
        assert data["operation_type"] == "update"
        
        # Verify updates
        tasks = data["successful_tasks"]
        task_by_id = {task["id"]: task for task in tasks}
        
        # Check first task
        task1 = task_by_id[self.task_ids[0]]
        assert task1["title"] == "Updated Task 1"
        assert task1["status"] == "In Progress"
        
        # Check second task
        task2 = task_by_id[self.task_ids[1]]
        assert task2["description"] == "Updated description"
        assert task2["epic_id"] == self.epic_id
        
        # Check third task
        task3 = task_by_id[self.task_ids[2]]
        assert task3["status"] == "Done"
        assert task3["assignee"] == "test-user"

    def test_bulk_update_tasks_with_status_changes(self):
        """Test that status changes create history entries."""
        bulk_request = {
            "updates": [
                {
                    "id": self.task_ids[0],
                    "update": {
                        "status": "In Progress"
                    }
                },
                {
                    "id": self.task_ids[1],
                    "update": {
                        "status": "Done"
                    }
                }
            ]
        }
        
        response = client.put(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        tasks = data["successful_tasks"]
        
        # Both tasks should have status history entries
        for task in tasks:
            # Should have at least one status change
            status_changes = [h for h in task["status_history"] if h["old_status"] != h["new_status"]]
            assert len(status_changes) >= 1

    def test_bulk_update_tasks_nonexistent_task(self):
        """Test bulk update with non-existent task ID."""
        bulk_request = {
            "updates": [
                {
                    "id": self.task_ids[0],
                    "update": {
                        "title": "Valid Update"
                    }
                },
                {
                    "id": 99999,  # Non-existent task
                    "update": {
                        "title": "Invalid Update"
                    }
                }
            ]
        }
        
        response = client.put(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 2
        assert data["total_successful"] == 1
        assert data["total_failed"] == 1
        
        # Check successful update
        assert len(data["successful_tasks"]) == 1
        assert data["successful_tasks"][0]["title"] == "Valid Update"
        
        # Check failed update
        assert len(data["failed_items"]) == 1
        failed_item = data["failed_items"][0]
        assert failed_item["item_id"] == 99999
        assert failed_item["error_code"] == "TASK_NOT_FOUND"

    def test_bulk_update_tasks_invalid_epic(self):
        """Test bulk update with invalid epic ID."""
        bulk_request = {
            "updates": [
                {
                    "id": self.task_ids[0],
                    "update": {
                        "epic_id": 99999  # Non-existent epic
                    }
                }
            ]
        }
        
        response = client.put(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_successful"] == 0
        assert data["total_failed"] == 1
        
        failed_item = data["failed_items"][0]
        assert failed_item["error_code"] == "EPIC_NOT_FOUND"

    def test_bulk_update_tasks_empty_updates(self):
        """Test bulk update with empty updates list."""
        bulk_request = {"updates": []}
        
        response = client.put(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 0
        assert data["total_successful"] == 0
        assert data["total_failed"] == 0

    def test_bulk_update_tasks_partial_update(self):
        """Test bulk update with partial field updates."""
        bulk_request = {
            "updates": [
                {
                    "id": self.task_ids[0],
                    "update": {
                        "title": "Only Title Updated"
                        # Don't update description, status, etc.
                    }
                }
            ]
        }
        
        response = client.put(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        updated_task = data["successful_tasks"][0]
        
        # Title should be updated
        assert updated_task["title"] == "Only Title Updated"
        
        # Other fields should remain unchanged - we'll get original values from DB
        with TestingSessionLocal() as db:
            original_task = db.query(models.Task).filter(models.Task.id == self.task_ids[0]).first()
            assert updated_task["description"] == original_task.description
            assert updated_task["status"] == original_task.status.value


class TestBulkTaskEdgeCases:
    """Test edge cases and error scenarios for bulk task operations."""

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

    def test_bulk_create_tasks_large_batch(self):
        """Test bulk creation with a large number of tasks."""
        tasks = [{"title": f"Task {i}", "description": f"Description {i}"} for i in range(100)]
        bulk_request = {"tasks": tasks}
        
        response = client.post(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requested"] == 100
        assert data["total_successful"] == 100
        assert data["total_failed"] == 0

    def test_bulk_tasks_malformed_request(self):
        """Test bulk operations with malformed request data."""
        # Missing required 'tasks' field
        response = client.post(f"/{self.project_id}/tasks/bulk", json={})
        assert response.status_code == 422
        
        # Invalid data type for tasks
        response = client.post(f"/{self.project_id}/tasks/bulk", json={"tasks": "invalid"})
        assert response.status_code == 422

    def test_bulk_tasks_unicode_content(self):
        """Test bulk operations with unicode content."""
        bulk_request = {
            "tasks": [
                {
                    "title": "Unicode Test: 测试任务 🚀",
                    "description": "Description with emojis 🎉 and unicode characters: ñáéíóú"
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_successful"] == 1
        task = data["successful_tasks"][0]
        assert "测试任务 🚀" in task["title"]
        assert "🎉" in task["description"]

    def test_bulk_tasks_very_long_content(self):
        """Test bulk operations with very long content."""
        long_title = "A" * 1000
        long_description = "B" * 5000
        
        bulk_request = {
            "tasks": [
                {
                    "title": long_title,
                    "description": long_description
                }
            ]
        }
        
        response = client.post(f"/{self.project_id}/tasks/bulk", json=bulk_request)
        
        # Should succeed (assuming no length limits in schema)
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_successful"] == 1
        task = data["successful_tasks"][0]
        assert len(task["title"]) == 1000
        assert len(task["description"]) == 5000

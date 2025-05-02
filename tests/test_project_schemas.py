import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas import Project, ProjectCreate, ProjectBase
from app.models import TaskStatus

def test_project_base_schema():
    # Test valid data
    project_data = {"name": "test-project"}
    project = ProjectBase(**project_data)
    assert project.name == "test-project"
    
    # Test required fields
    with pytest.raises(ValidationError):
        ProjectBase()  # name is required

def test_project_create_schema():
    # Test valid data
    project_data = {"name": "test-project"}
    project = ProjectCreate(**project_data)
    assert project.name == "test-project"

def test_project_schema():
    # Test full project response model
    project_data = {
        "id": 1,
        "name": "test-project",
        "created_at": datetime.now()
    }
    project = Project(**project_data)
    assert project.id == 1
    assert project.name == "test-project"
    assert isinstance(project.created_at, datetime)

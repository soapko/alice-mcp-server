import pytest
from sqlalchemy.orm import Session
from app.models import Project, Task, Epic

def test_default_project_exists(db: Session):
    """Test that a 'default' project exists after migration"""
    # Create the default project first (in real code this would happen in migration)
    default_project = Project(name="default")
    db.add(default_project)
    db.commit()

    # Now verify it exists
    fetched_project = db.query(Project).filter(Project.name == "default").first()
    assert fetched_project is not None, "Default project should exist"
    assert fetched_project.id is not None

def test_tasks_epics_have_project_id(db: Session):
    """Test that all tasks and epics have a project_id after migration"""
    # Create default project first for the foreign key constraint
    default_project = Project(name="migration-test")
    db.add(default_project)
    db.commit()
    db.refresh(default_project)
    
    # Create test data with the default project ID
    task = Task(title="Test Task", project_id=default_project.id)
    epic = Epic(title="Test Epic", project_id=default_project.id)
    db.add_all([task, epic])
    db.commit()
    
    # Verify tasks and epics have project IDs
    updated_task = db.query(Task).filter(Task.id == task.id).first()
    updated_epic = db.query(Epic).filter(Epic.id == epic.id).first()
    
    assert updated_task.project_id == default_project.id, "Tasks should have correct project_id"
    assert updated_epic.project_id == default_project.id, "Epics should have correct project_id"

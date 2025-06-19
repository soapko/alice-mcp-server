from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models

def test_update_priority_plan(client: TestClient, db: Session):
    # Create a project and tasks
    project = models.Project(name="Test Project for Plan")
    db.add(project)
    db.commit()
    db.refresh(project)

    task1 = models.Task(title="Task 1", project_id=project.id)
    task2 = models.Task(title="Task 2", project_id=project.id)
    db.add_all([task1, task2])
    db.commit()
    db.refresh(task1)
    db.refresh(task2)

    plan_updates = [
        {"task_id": task1.id, "rationale": "First task"},
        {"task_id": task2.id, "rationale": "Second task"},
    ]

    response = client.put(
        f"/{project.id}/priority-plan/",
        json=plan_updates
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["task"]["id"] == task1.id
    assert data[0]["position"] == 0
    assert data[1]["task"]["id"] == task2.id
    assert data[1]["position"] == 1

def test_get_priority_plan(client: TestClient, db: Session):
    project = models.Project(name="Test Project for Getting Plan")
    db.add(project)
    db.commit()
    db.refresh(project)

    task1 = models.Task(title="Task 1", project_id=project.id)
    db.add(task1)
    db.commit()
    db.refresh(task1)

    client.put(
        f"/{project.id}/priority-plan/",
        json=[{"task_id": task1.id, "rationale": "Only task"}]
    )

    response = client.get(f"/{project.id}/priority-plan/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task"]["title"] == "Task 1"

def test_get_next_task(client: TestClient, db: Session):
    project = models.Project(name="Test Project for Next Task")
    db.add(project)
    db.commit()
    db.refresh(project)

    task1 = models.Task(title="Task 1", project_id=project.id, status=models.TaskStatus.DONE)
    task2 = models.Task(title="Task 2", project_id=project.id, status=models.TaskStatus.TODO)
    db.add_all([task1, task2])
    db.commit()
    db.refresh(task1)
    db.refresh(task2)

    client.put(
        f"/{project.id}/priority-plan/",
        json=[
            {"task_id": task1.id, "rationale": "Done task"},
            {"task_id": task2.id, "rationale": "Todo task"},
        ]
    )

    response = client.get(f"/{project.id}/priority-plan/next-task")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Task 2"

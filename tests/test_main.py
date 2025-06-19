from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import TaskStatus, Project

def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Alice MCP Server"}

# --- Task Tests --- 

def test_create_task(client: TestClient, db: Session):
    project = Project(name="test_create_task_project")
    db.add(project)
    db.commit()
    db.refresh(project)

    response = client.post(
        f"/{project.id}/tasks/",
        json={"title": "Test Task", "description": "Test Description"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert data["status"] == TaskStatus.TODO.value
    assert "id" in data
    assert "created_at" in data
    assert len(data["status_history"]) == 1 # Check initial status history
    assert data["status_history"][0]["new_status"] == TaskStatus.TODO.value

def test_read_tasks(client: TestClient, db: Session):
    project = Project(name="test_read_tasks_project")
    db.add(project)
    db.commit()
    db.refresh(project)
    # Create a task first
    client.post(f"/{project.id}/tasks/", json={"title": "Task 1"})
    client.post(f"/{project.id}/tasks/", json={"title": "Task 2", "status": TaskStatus.IN_PROGRESS.value})

    response = client.get(f"/{project.id}/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Check default sorting (newest first)
    assert data[0]["title"] == "Task 2"
    assert data[1]["title"] == "Task 1"

def test_read_task(client: TestClient, db: Session):
    project = Project(name="test_read_task_project")
    db.add(project)
    db.commit()
    db.refresh(project)
    create_response = client.post(f"/{project.id}/tasks/", json={"title": "Specific Task"})
    task_id = create_response.json()["id"]

    response = client.get(f"/{project.id}/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Specific Task"
    assert data["id"] == task_id
    assert len(data["messages"]) == 0
    assert len(data["status_history"]) == 1

def test_update_task(client: TestClient, db: Session):
    project = Project(name="test_update_task_project")
    db.add(project)
    db.commit()
    db.refresh(project)
    create_response = client.post(f"/{project.id}/tasks/", json={"title": "Update Me"})
    task_id = create_response.json()["id"]

    update_payload = {"title": "Updated Title", "status": TaskStatus.DONE.value}
    response = client.put(f"/{project.id}/tasks/{task_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == TaskStatus.DONE.value
    assert len(data["status_history"]) == 2 # Initial + Update
    assert data["status_history"][1]["old_status"] == TaskStatus.TODO.value
    assert data["status_history"][1]["new_status"] == TaskStatus.DONE.value

def test_delete_task(client: TestClient, db: Session):
    project = Project(name="test_delete_task_project")
    db.add(project)
    db.commit()
    db.refresh(project)
    create_response = client.post(f"/{project.id}/tasks/", json={"title": "Delete Me"})
    task_id = create_response.json()["id"]

    delete_response = client.delete(f"/{project.id}/tasks/{task_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/{project.id}/tasks/{task_id}")
    assert get_response.status_code == 404

# --- Message Tests --- 

def test_create_message_for_task(client: TestClient, db: Session):
    project = Project(name="test_create_message_project")
    db.add(project)
    db.commit()
    db.refresh(project)
    create_task_response = client.post(f"/{project.id}/tasks/", json={"title": "Task with Message"})
    task_id = create_task_response.json()["id"]

    response = client.post(
        f"/{project.id}/tasks/{task_id}/messages/",
        json={"author": "Test Author", "message": "Test Message Content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["author"] == "Test Author"
    assert data["message"] == "Test Message Content"
    assert data["task_id"] == task_id
    assert "id" in data
    assert "timestamp" in data

def test_read_messages_for_task(client: TestClient, db: Session):
    project = Project(name="test_read_messages_project")
    db.add(project)
    db.commit()
    db.refresh(project)
    create_task_response = client.post(f"/{project.id}/tasks/", json={"title": "Task with Multiple Messages"})
    task_id = create_task_response.json()["id"]

    client.post(f"/{project.id}/tasks/{task_id}/messages/", json={"author": "A1", "message": "M1"})
    client.post(f"/{project.id}/tasks/{task_id}/messages/", json={"author": "A2", "message": "M2"})

    response = client.get(f"/{project.id}/tasks/{task_id}/messages/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["message"] == "M1"
    assert data[1]["message"] == "M2"

# --- Status History Test --- 

def test_read_status_history(client: TestClient, db: Session):
    project = Project(name="test_status_history_project")
    db.add(project)
    db.commit()
    db.refresh(project)
    create_response = client.post(f"/{project.id}/tasks/", json={"title": "History Task"})
    task_id = create_response.json()["id"]

    client.put(f"/{project.id}/tasks/{task_id}", json={"status": TaskStatus.IN_PROGRESS.value})
    client.put(f"/{project.id}/tasks/{task_id}", json={"status": TaskStatus.DONE.value})

    response = client.get(f"/{project.id}/tasks/{task_id}/status-history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3 # Create, In Progress, Done
    assert data[0]["new_status"] == TaskStatus.TODO.value
    assert data[1]["old_status"] == TaskStatus.TODO.value
    assert data[1]["new_status"] == TaskStatus.IN_PROGRESS.value
    assert data[2]["old_status"] == TaskStatus.IN_PROGRESS.value
    assert data[2]["new_status"] == TaskStatus.DONE.value


# TODO: Add tests for filtering, edge cases, and error handling

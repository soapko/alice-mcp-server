import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import TaskStatus, Project

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Use StaticPool for SQLite in-memory tests
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for testing
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine) # Clean up

@pytest.fixture(scope="function")
def default_project(db_session):
    """Create a 'default' project for testing"""
    project = Project(name="default")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project

@pytest.fixture(scope="function")
def test_client(db_session, default_project):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    # Clean up overrides after test function finishes
    app.dependency_overrides.clear()



def test_read_root(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Alice MCP Server"}

# --- Task Tests --- 

def test_create_task(test_client):
    response = test_client.post(
        "/default/tasks/",
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

def test_read_tasks(test_client):
    # Create a task first
    test_client.post("/default/tasks/", json={"title": "Task 1"})
    test_client.post("/default/tasks/", json={"title": "Task 2", "status": TaskStatus.IN_PROGRESS.value})

    response = test_client.get("/default/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Check default sorting (newest first)
    assert data[0]["title"] == "Task 2"
    assert data[1]["title"] == "Task 1"

def test_read_task(test_client):
    create_response = test_client.post("/default/tasks/", json={"title": "Specific Task"})
    task_id = create_response.json()["id"]

    response = test_client.get(f"/default/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Specific Task"
    assert data["id"] == task_id
    assert len(data["messages"]) == 0
    assert len(data["status_history"]) == 1

def test_update_task(test_client):
    create_response = test_client.post("/default/tasks/", json={"title": "Update Me"})
    task_id = create_response.json()["id"]

    update_payload = {"title": "Updated Title", "status": TaskStatus.DONE.value}
    response = test_client.put(f"/default/tasks/{task_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == TaskStatus.DONE.value
    assert len(data["status_history"]) == 2 # Initial + Update
    assert data["status_history"][1]["old_status"] == TaskStatus.TODO.value
    assert data["status_history"][1]["new_status"] == TaskStatus.DONE.value

def test_delete_task(test_client):
    create_response = test_client.post("/default/tasks/", json={"title": "Delete Me"})
    task_id = create_response.json()["id"]

    delete_response = test_client.delete(f"/default/tasks/{task_id}")
    assert delete_response.status_code == 204

    get_response = test_client.get(f"/default/tasks/{task_id}")
    assert get_response.status_code == 404

# --- Message Tests --- 

def test_create_message_for_task(test_client):
    create_task_response = test_client.post("/default/tasks/", json={"title": "Task with Message"})
    task_id = create_task_response.json()["id"]

    response = test_client.post(
        f"/default/tasks/{task_id}/messages/",
        json={"author": "Test Author", "message": "Test Message Content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["author"] == "Test Author"
    assert data["message"] == "Test Message Content"
    assert data["task_id"] == task_id
    assert "id" in data
    assert "timestamp" in data

def test_read_messages_for_task(test_client):
    create_task_response = test_client.post("/default/tasks/", json={"title": "Task with Multiple Messages"})
    task_id = create_task_response.json()["id"]

    test_client.post(f"/default/tasks/{task_id}/messages/", json={"author": "A1", "message": "M1"})
    test_client.post(f"/default/tasks/{task_id}/messages/", json={"author": "A2", "message": "M2"})

    response = test_client.get(f"/default/tasks/{task_id}/messages/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["message"] == "M1"
    assert data[1]["message"] == "M2"

# --- Status History Test --- 

def test_read_status_history(test_client):
    create_response = test_client.post("/default/tasks/", json={"title": "History Task"})
    task_id = create_response.json()["id"]

    test_client.put(f"/default/tasks/{task_id}", json={"status": TaskStatus.IN_PROGRESS.value})
    test_client.put(f"/default/tasks/{task_id}", json={"status": TaskStatus.DONE.value})

    response = test_client.get(f"/default/tasks/{task_id}/status-history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3 # Create, In Progress, Done
    assert data[0]["new_status"] == TaskStatus.TODO.value
    assert data[1]["old_status"] == TaskStatus.TODO.value
    assert data[1]["new_status"] == TaskStatus.IN_PROGRESS.value
    assert data[2]["old_status"] == TaskStatus.IN_PROGRESS.value
    assert data[2]["new_status"] == TaskStatus.DONE.value


# TODO: Add tests for filtering, edge cases, and error handling

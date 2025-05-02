import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Project, Task

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_project(db_session):
    """Create a test project for testing"""
    project = Project(name="test-project-api")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project

def test_create_project(test_client):
    """Test creating a new project via API"""
    response = test_client.post(
        "/projects/",
        json={"name": "project-1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "project-1"
    assert "id" in data
    assert "created_at" in data

def test_create_project_duplicate_name(test_client, test_project):
    """Test that creating a project with a duplicate name fails"""
    response = test_client.post(
        "/projects/",
        json={"name": test_project.name}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_read_projects(test_client, test_project):
    """Test getting a list of projects"""
    response = test_client.get("/projects/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # The test_project should be in the list
    assert any(project["name"] == test_project.name for project in data)

def test_read_project_by_id(test_client, test_project):
    """Test getting a specific project by ID"""
    response = test_client.get(f"/projects/{test_project.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_project.id
    assert data["name"] == test_project.name

def test_read_project_by_name(test_client, test_project):
    """Test getting a specific project by name"""
    response = test_client.get(f"/projects/by-name/{test_project.name}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_project.id
    assert data["name"] == test_project.name

def test_read_nonexistent_project(test_client):
    """Test that trying to get a nonexistent project returns 404"""
    response = test_client.get("/projects/9999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    response = test_client.get("/projects/by-name/nonexistent-project")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

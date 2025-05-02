import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Project, TaskStatus

# Use an in-memory SQLite database for testing (same as test_main.py)
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

def test_create_project(db_session):
    """Test creating a Project directly with SQLAlchemy"""
    new_project = Project(name="test-project")
    db_session.add(new_project)
    db_session.commit()
    db_session.refresh(new_project)
    
    assert new_project.id is not None
    assert new_project.name == "test-project"
    assert new_project.created_at is not None

def test_project_name_unique(db_session):
    """Test that project names must be unique"""
    project1 = Project(name="unique-test")
    db_session.add(project1)
    db_session.commit()
    
    # Trying to add another project with the same name should fail
    project2 = Project(name="unique-test")
    db_session.add(project2)
    
    with pytest.raises(Exception):  # SQLite will raise an IntegrityError
        db_session.commit()
    db_session.rollback()

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import models

def test_create_decision(client: TestClient, db: Session):
    # Create a project first
    project = models.Project(name="Test Project for Decisions")
    db.add(project)
    db.commit()
    db.refresh(project)

    response = client.post(
        f"/{project.id}/decisions/",
        json={"title": "Test Decision", "context_md": "Some context", "decision_md": "A decision was made", "consequences_md": "Things will happen"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Decision"
    assert data["project_id"] == project.id

def test_read_decisions(client: TestClient, db: Session):
    project = models.Project(name="Test Project for Reading Decisions")
    db.add(project)
    db.commit()
    db.refresh(project)

    client.post(
        f"/{project.id}/decisions/",
        json={"title": "Test Decision 1", "context_md": "Some context", "decision_md": "A decision was made", "consequences_md": "Things will happen"}
    )
    client.post(
        f"/{project.id}/decisions/",
        json={"title": "Test Decision 2", "context_md": "Some context", "decision_md": "A decision was made", "consequences_md": "Things will happen"}
    )

    response = client.get(f"/{project.id}/decisions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_read_decision(client: TestClient, db: Session):
    project = models.Project(name="Test Project for Reading One Decision")
    db.add(project)
    db.commit()
    db.refresh(project)

    post_response = client.post(
        f"/{project.id}/decisions/",
        json={"title": "A Single Decision", "context_md": "Some context", "decision_md": "A decision was made", "consequences_md": "Things will happen"}
    )
    decision_id = post_response.json()["id"]

    response = client.get(f"/{project.id}/decisions/{decision_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "A Single Decision"

def test_update_decision(client: TestClient, db: Session):
    project = models.Project(name="Test Project for Updating Decision")
    db.add(project)
    db.commit()
    db.refresh(project)

    post_response = client.post(
        f"/{project.id}/decisions/",
        json={"title": "Initial Title", "context_md": "Some context", "decision_md": "A decision was made", "consequences_md": "Things will happen"}
    )
    decision_id = post_response.json()["id"]

    response = client.put(
        f"/{project.id}/decisions/{decision_id}",
        json={"title": "Updated Title"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"

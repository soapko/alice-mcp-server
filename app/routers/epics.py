from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from .. import schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/{project_id}/epics",
    tags=["epics"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Epic)
def create_epic(
    project_id: str = Path(..., description="The ID of the project to create the epic in"),
    epic: schemas.EpicCreate = None, 
    db: Session = Depends(get_db)
):
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.name == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    # Create epic data with project_id
    epic_data = epic.model_dump()
    epic_data["project_id"] = db_project.id
    db_epic = models.Epic(**epic_data)
    db.add(db_epic)
    db.commit()
    db.refresh(db_epic)
    return db_epic

@router.get("/", response_model=List[schemas.Epic])
def read_epics(
    project_id: str = Path(..., description="The ID of the project to fetch epics from"),
    skip: int = 0,
    limit: int = 100,
    status: Optional[models.TaskStatus] = Query(None),
    assignee: Optional[str] = Query(None),
    created_after: Optional[datetime] = Query(None, description="Filter epics created after this timestamp (ISO 8601 format)"),
    created_before: Optional[datetime] = Query(None, description="Filter epics created before this timestamp (ISO 8601 format)"),
    db: Session = Depends(get_db)
):
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.name == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    query = (
        db.query(models.Epic)
        .filter(models.Epic.project_id == db_project.id)  # Filter by project_id
        .order_by(models.Epic.id.desc())  # Default sort: newest first by ID
    )
    
    if status:
        query = query.filter(models.Epic.status == status)
    if assignee:
        query = query.filter(models.Epic.assignee == assignee)
    if created_after:
        query = query.filter(models.Epic.created_at > created_after)
    if created_before:
        query = query.filter(models.Epic.created_at < created_before)
        
    epics = query.offset(skip).limit(limit).all()
    return epics

@router.get("/{epic_id}", response_model=schemas.Epic)
def read_epic(
    epic_id: int, 
    project_id: str = Path(..., description="The ID of the project the epic belongs to"),
    db: Session = Depends(get_db)
):
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.name == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    # Find epic by both ID and project_id
    db_epic = db.query(models.Epic).filter(
        models.Epic.id == epic_id,
        models.Epic.project_id == db_project.id
    ).first()
    if db_epic is None:
        raise HTTPException(status_code=404, detail="Epic not found")
    return db_epic

@router.put("/{epic_id}", response_model=schemas.Epic)
def update_epic(
    epic_id: int, 
    epic: schemas.EpicUpdate, 
    project_id: str = Path(..., description="The ID of the project the epic belongs to"),
    db: Session = Depends(get_db)
):
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.name == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    # Find epic by both ID and project_id
    db_epic = db.query(models.Epic).filter(
        models.Epic.id == epic_id,
        models.Epic.project_id == db_project.id
    ).first()
    if db_epic is None:
        raise HTTPException(status_code=404, detail="Epic not found")

    update_data = epic.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_epic, key, value)

    db.commit()
    db.refresh(db_epic)
    return db_epic

@router.delete("/{epic_id}", status_code=204)
def delete_epic(
    epic_id: int, 
    project_id: str = Path(..., description="The ID of the project the epic belongs to"),
    db: Session = Depends(get_db)
):
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.name == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    # Find epic by both ID and project_id
    db_epic = db.query(models.Epic).filter(
        models.Epic.id == epic_id,
        models.Epic.project_id == db_project.id
    ).first()
    if db_epic is None:
        raise HTTPException(status_code=404, detail="Epic not found")
    
    # Update any tasks associated with this epic to have epic_id=None
    # But only within the same project
    db.query(models.Task).filter(
        models.Task.epic_id == epic_id,
        models.Task.project_id == db_project.id
    ).update({"epic_id": None})
    
    db.delete(db_epic)
    db.commit()
    return None

@router.get("/{epic_id}/tasks", response_model=List[schemas.Task])
def read_epic_tasks(
    epic_id: int, 
    project_id: str = Path(..., description="The ID of the project the epic belongs to"),
    db: Session = Depends(get_db)
):
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.name == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    # Find epic by both ID and project_id
    db_epic = db.query(models.Epic).filter(
        models.Epic.id == epic_id,
        models.Epic.project_id == db_project.id
    ).first()
    if db_epic is None:
        raise HTTPException(status_code=404, detail="Epic not found")
    
    tasks = (
        db.query(models.Task)
        .options(joinedload(models.Task.messages), joinedload(models.Task.status_history))
        .filter(
            models.Task.epic_id == epic_id,
            models.Task.project_id == db_project.id
        )
        .all()
    )
    return tasks

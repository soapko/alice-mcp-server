from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/{project_id}/tasks/{task_id}/messages",
    tags=["messages"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Message)
def create_message_for_task(
    task_id: int, 
    message: schemas.MessageCreate, 
    project_id: str = Path(..., description="The ID of the project the task belongs to"),
    db: Session = Depends(get_db)
):
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.name == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    # Find task by both ID and project_id
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.project_id == db_project.id
    ).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db_message = models.Message(**message.model_dump(), task_id=task_id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

@router.get("/", response_model=List[schemas.Message])
def read_messages_for_task(
    task_id: int, 
    project_id: str = Path(..., description="The ID of the project the task belongs to"),
    db: Session = Depends(get_db)
):
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.name == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    
    # Find task by both ID and project_id
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.project_id == db_project.id
    ).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Ensure messages are ordered chronologically
    messages = db.query(models.Message).filter(models.Message.task_id == task_id).order_by(models.Message.timestamp).all()
    return messages

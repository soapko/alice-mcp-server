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
    project_id: int = Path(..., description="The NUMERIC ID of the project the task belongs to"), # Changed to int
    db: Session = Depends(get_db)
):
    # Verify project exists by its numeric ID
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first() # Changed to filter by models.Project.id
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project with numeric ID '{project_id}' not found") # Updated error message
    
    # Find task by both ID and project_id (which is now numeric)
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.project_id == project_id # project_id is now numeric
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
    project_id: int = Path(..., description="The NUMERIC ID of the project the task belongs to"), # Changed to int
    db: Session = Depends(get_db)
):
    # Verify project exists by its numeric ID
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first() # Changed to filter by models.Project.id
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project with numeric ID '{project_id}' not found") # Updated error message
    
    # Find task by both ID and project_id (which is now numeric)
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.project_id == project_id # project_id is now numeric
    ).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Ensure messages are ordered chronologically
    messages = db.query(models.Message).filter(models.Message.task_id == task_id).order_by(models.Message.timestamp).all()
    return messages

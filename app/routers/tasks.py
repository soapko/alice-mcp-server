from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from .. import schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/{project_id}/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Task)
def create_task(
    project_id: int = Path(..., description="The NUMERIC ID of the project to create the task in"), # Changed to int
    task: schemas.TaskCreate = None, 
    db: Session = Depends(get_db)
):
    # Verify project exists by its numeric ID
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first() # Changed to filter by models.Project.id
    if db_project is None:
        # If project not found by numeric ID, it's an error. Auto-creation removed.
        raise HTTPException(status_code=404, detail=f"Project with numeric ID '{project_id}' not found")
    # Validate epic_id if provided, and ensure it belongs to the same project
    if task.epic_id is not None:
        db_epic = db.query(models.Epic).filter(
            models.Epic.id == task.epic_id,
            models.Epic.project_id == db_project.id # This uses the numeric project.id
        ).first()
        if db_epic is None:
            raise HTTPException(status_code=404, detail="Epic not found")
    
    # Create task data with project_id
    task_data = task.model_dump()
    task_data["project_id"] = db_project.id # This uses the numeric project.id
    db_task = models.Task(**task_data)
    # Initial status history entry
    initial_history = models.StatusHistory(
        task=db_task,
        old_status=task.status, # Using initial status as old for creation event
        new_status=task.status
    )
    db.add(db_task)
    db.add(initial_history)
    db.commit()
    db.refresh(db_task)
    # Eager load relationships for the response model
    db.refresh(db_task, attribute_names=['messages', 'status_history'])
    return db_task

@router.get("/", response_model=List[schemas.Task])
def read_tasks(
    project_id: int = Path(..., description="The NUMERIC ID of the project to fetch tasks from"), # Changed to int
    skip: int = 0,
    limit: int = 100,
    status: Optional[models.TaskStatus] = Query(None),
    assignee: Optional[str] = Query(None),
    epic_id: Optional[int] = Query(None, description="Filter tasks by epic ID"),
    created_after: Optional[datetime] = Query(None, description="Filter tasks created after this timestamp (ISO 8601 format)"),
    created_before: Optional[datetime] = Query(None, description="Filter tasks created before this timestamp (ISO 8601 format)"),
    include_details: bool = Query(True, description="Whether to include messages and status history in the response"),
    db: Session = Depends(get_db)
):
    """
    Get tasks for a specific project with various filtering options.
    
    Set include_details=false to get a simplified response without messages and status history.
    """
    # Verify project exists by its numeric ID
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first() # Changed to filter by models.Project.id
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project with numeric ID '{project_id}' not found") # Updated error message
    
    # Base query
    query = db.query(models.Task).filter(models.Task.project_id == db_project.id) # This uses the numeric project.id
    
    # Always load the relationships, but we'll clear them later if include_details is False
    query = query.options(
        joinedload(models.Task.messages),
        joinedload(models.Task.status_history)
    )
    
    # Apply ordering
    query = query.order_by(models.Task.id.desc())  # Default sort: newest first by ID
    
    if status:
        query = query.filter(models.Task.status == status)
    if assignee:
        query = query.filter(models.Task.assignee == assignee)
    if epic_id:
        query = query.filter(models.Task.epic_id == epic_id)
    if created_after:
        query = query.filter(models.Task.created_at > created_after)
    if created_before:
        query = query.filter(models.Task.created_at < created_before)
        
    tasks = query.offset(skip).limit(limit).all()
    
    # If include_details is False, clear the messages and status_history collections
    # This will save bandwidth while still using the Task response model
    if not include_details:
        for task in tasks:
            task.messages = []
            task.status_history = []
    
    return tasks

@router.get("/{task_id}", response_model=schemas.Task)
def read_task(
    task_id: int, 
    project_id: int = Path(..., description="The NUMERIC ID of the project the task belongs to"), # Changed to int
    db: Session = Depends(get_db)
):
    # Verify project exists by its numeric ID
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first() # Changed to filter by models.Project.id
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project with numeric ID '{project_id}' not found") # Updated error message
    # Use options for eager loading relationships and filter by both task_id and project_id
    db_task = (
        db.query(models.Task)
        .options(
            joinedload(models.Task.messages), 
            joinedload(models.Task.status_history)
        )
        .filter(
            models.Task.id == task_id,
            models.Task.project_id == project_id # project_id is now numeric
        )
        .first()
    )
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.put("/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int, 
    task: schemas.TaskUpdate, 
    project_id: int = Path(..., description="The NUMERIC ID of the project the task belongs to"), # Changed to int
    db: Session = Depends(get_db)
):
    # Verify project exists by its numeric ID
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first() # Changed to filter by models.Project.id
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project with numeric ID '{project_id}' not found") # Updated error message
    
    # Find task by both ID and project_id
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.project_id == project_id # project_id is now numeric
    ).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # Validate epic_id if provided and ensure it belongs to the same project
    if task.epic_id is not None:
        db_epic = db.query(models.Epic).filter(
            models.Epic.id == task.epic_id,
            models.Epic.project_id == project_id # project_id is now numeric
        ).first()
        if db_epic is None:
            raise HTTPException(status_code=404, detail="Epic not found")

    update_data = task.model_dump(exclude_unset=True)
    old_status = db_task.status

    for key, value in update_data.items():
        setattr(db_task, key, value)

    # Add status history if status changed
    if 'status' in update_data and update_data['status'] != old_status:
        status_change = models.StatusHistory(
            task_id=task_id,
            old_status=old_status,
            new_status=update_data['status']
        )
        db.add(status_change)

    db.commit()
    db.refresh(db_task)
    # Eager load relationships for the response model
    db.refresh(db_task, attribute_names=['messages', 'status_history'])
    return db_task

@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int, 
    project_id: int = Path(..., description="The NUMERIC ID of the project the task belongs to"), # Changed to int
    db: Session = Depends(get_db)
):
    # Verify project exists by its numeric ID
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first() # Changed to filter by models.Project.id
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project with numeric ID '{project_id}' not found") # Updated error message
    
    # Find task by both ID and project_id 
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.project_id == project_id # project_id is now numeric
    ).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    # Optionally delete related messages and status history or handle via cascade delete in DB
    db.delete(db_task)
    db.commit()
    return None

@router.get("/{task_id}/status-history", response_model=List[schemas.StatusHistory])
def read_status_history(
    task_id: int, 
    project_id: int = Path(..., description="The NUMERIC ID of the project the task belongs to"), # Changed to int
    db: Session = Depends(get_db)
):
    # Verify project exists by its numeric ID
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first() # Changed to filter by models.Project.id
    if db_project is None:
        raise HTTPException(status_code=404, detail=f"Project with numeric ID '{project_id}' not found") # Updated error message
    
    # Find task by both ID and project_id
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.project_id == project_id # project_id is now numeric
    ).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task.status_history

@router.put("/{task_id}/move/{new_project_id_str}", response_model=schemas.Task) # Renamed new_project_id to new_project_id_str
def move_task_to_project(
    task_id: int, 
    new_project_id_str: str = Path(..., alias="new_project_id", description="The NAME or SLUG of the destination project"), # Kept as string for name lookup
    project_id: int = Path(..., description="The NUMERIC ID of the current project the task belongs to"), # Changed to int
    db: Session = Depends(get_db)
):
    """
    Move a task from one project to another.
    
    This endpoint allows moving a task between projects. Epic associations will be
    removed since epics are project-specific.
    
    Parameters:
    - task_id: ID of the task to move
    - new_project_id_str: Name of the destination project (looked up by name)
    - project_id: Current project's NUMERIC ID (from path)
    """
    # Verify source project exists by its numeric ID
    source_project = db.query(models.Project).filter(models.Project.id == project_id).first() # Changed to filter by models.Project.id
    if source_project is None:
        raise HTTPException(status_code=404, detail=f"Source project with numeric ID '{project_id}' not found") # Updated error message
    
    # Verify target project exists by its NAME
    target_project = db.query(models.Project).filter(models.Project.name == new_project_id_str).first()
    if target_project is None:
        raise HTTPException(status_code=404, detail=f"Target project '{new_project_id_str}' not found")
    
    # Find task by both ID and source project_id (numeric)
    db_task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.project_id == project_id # project_id is numeric
    ).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found in source project")
    
    # Update task with new project ID and reset epic_id (epics are project-specific)
    db_task.project_id = target_project.id
    db_task.epic_id = None
    
    db.commit()
    db.refresh(db_task)
    
    # Eager load relationships for the response model
    db.refresh(db_task, attribute_names=['messages', 'status_history'])
    return db_task

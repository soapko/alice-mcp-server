from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload
from typing import List

from .. import schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/{project_id}/priority-plan",
    tags=["project-plan"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.ProjectPlanEntry])
def get_priority_plan(
    project_id: int,
    db: Session = Depends(get_db)
):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    plan_entries = db.query(models.TaskPriority).filter(models.TaskPriority.project_id == project_id).order_by(models.TaskPriority.position).options(joinedload(models.TaskPriority.task)).all()
    
    result = []
    for entry in plan_entries:
        result.append(schemas.ProjectPlanEntry(
            task=entry.task,
            rationale=entry.rationale,
            position=entry.position
        ))
    return result

@router.put("/", response_model=List[schemas.ProjectPlanEntry])
def update_priority_plan(
    project_id: int,
    plan_updates: List[schemas.ProjectPlanUpdate],
    db: Session = Depends(get_db)
):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Clear existing plan
    db.query(models.TaskPriority).filter(models.TaskPriority.project_id == project_id).delete()

    for i, update in enumerate(plan_updates):
        db_task = db.query(models.Task).filter(models.Task.id == update.task_id, models.Task.project_id == project_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail=f"Task with id {update.task_id} not found in this project.")
        
        new_entry = models.TaskPriority(
            project_id=project_id,
            task_id=update.task_id,
            position=i,
            rationale=update.rationale
        )
        db.add(new_entry)
    
    db.commit()
    
    return get_priority_plan(project_id, db)

@router.get("/next-task", response_model=schemas.Task)
def get_next_task(
    project_id: int,
    db: Session = Depends(get_db)
):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    next_task_entry = db.query(models.TaskPriority).join(models.Task).filter(
        models.TaskPriority.project_id == project_id,
        models.Task.status.notin_([models.TaskStatus.DONE, models.TaskStatus.CANCELED])
    ).order_by(models.TaskPriority.position).first()

    if not next_task_entry:
        raise HTTPException(status_code=404, detail="No upcoming tasks in the plan.")

    return next_task_entry.task

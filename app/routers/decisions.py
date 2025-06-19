from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/{project_id}/decisions",
    tags=["decisions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Decision)
def create_decision(
    project_id: int,
    decision: schemas.DecisionCreate,
    db: Session = Depends(get_db)
):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_decision = models.Decision(**decision.model_dump(), project_id=project_id)
    db.add(db_decision)
    db.commit()
    db.refresh(db_decision)
    return db_decision

@router.get("/", response_model=List[schemas.Decision])
def read_decisions(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    decisions = db.query(models.Decision).filter(models.Decision.project_id == project_id).offset(skip).limit(limit).all()
    return decisions

@router.get("/{decision_id}", response_model=schemas.Decision)
def read_decision(
    project_id: int,
    decision_id: int,
    db: Session = Depends(get_db)
):
    db_decision = db.query(models.Decision).filter(models.Decision.project_id == project_id, models.Decision.id == decision_id).first()
    if db_decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return db_decision

@router.put("/{decision_id}", response_model=schemas.Decision)
def update_decision(
    project_id: int,
    decision_id: int,
    decision: schemas.DecisionUpdate,
    db: Session = Depends(get_db)
):
    db_decision = db.query(models.Decision).filter(models.Decision.project_id == project_id, models.Decision.id == decision_id).first()
    if db_decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")

    update_data = decision.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_decision, key, value)
    
    db.commit()
    db.refresh(db_decision)
    return db_decision

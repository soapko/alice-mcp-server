from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from .. import schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project.
    
    - **name**: Unique name identifier for the project (required)
    """
    # Check if a project with this name already exists
    db_project = db.query(models.Project).filter(models.Project.name == project.name).first()
    if db_project:
        raise HTTPException(status_code=400, detail="Project with this name already exists")
    
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=List[schemas.ProjectIdentifier]) # Changed response_model
def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get a list of all projects with their ID and name.
    
    Provides pagination with skip/limit parameters.
    """
    # Return project ID and name
    projects = db.query(models.Project.id, models.Project.name).order_by(models.Project.id).offset(skip).limit(limit).all()
    # FastAPI will map these to ProjectIdentifier schema
    return projects

@router.get("/{project_id}", response_model=schemas.Project)
def read_project(project_id: int, db: Session = Depends(get_db)):
    """
    Get details about a specific project by ID.
    
    - **project_id**: The ID of the project to retrieve
    """
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@router.get("/by-name/{project_name}", response_model=schemas.Project)
def read_project_by_name(project_name: str, db: Session = Depends(get_db)):
    """
    Get details about a specific project by name.
    
    - **project_name**: The name of the project to retrieve
    """
    db_project = db.query(models.Project).filter(models.Project.name == project_name).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

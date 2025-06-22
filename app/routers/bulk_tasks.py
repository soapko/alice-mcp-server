"""
Bulk task operations router for Alice MCP server.
Provides endpoints for creating and updating multiple tasks in single API calls.
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
from typing import Set

from .. import models
from ..database import get_db
from ..schemas_bulk import (
    BulkTaskCreate, BulkTaskUpdate, BulkTaskResult, 
    BulkOperationError, BulkErrorCode, BulkOperationType
)

router = APIRouter(
    prefix="/{project_id}",
    tags=["bulk-tasks"],
    responses={404: {"description": "Not found"}},
)

@router.post("/tasks/bulk", response_model=BulkTaskResult)
def bulk_create_tasks(
    bulk_request: BulkTaskCreate,
    project_id: int = Path(..., description="The NUMERIC ID of the project"),
    db: Session = Depends(get_db)
):
    """
    Create multiple tasks in a single request.
    
    Features:
    - Validates all tasks before creating any
    - Creates status history for each task
    - Validates epic_ids if provided
    - Returns detailed success/failure information
    """
    
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    
    successful_tasks = []
    failed_items = []
    
    # Pre-validate all epic_ids to avoid partial failures
    epic_ids = {task.epic_id for task in bulk_request.tasks if task.epic_id is not None}
    if epic_ids:
        valid_epics = set(
            db.query(models.Epic.id)
            .filter(models.Epic.id.in_(epic_ids), models.Epic.project_id == project_id)
            .all()
        )
        valid_epic_ids = {epic[0] for epic in valid_epics}
        invalid_epic_ids = epic_ids - valid_epic_ids
    else:
        invalid_epic_ids = set()
    
    # Process each task
    for index, task_data in enumerate(bulk_request.tasks):
        try:
            # Validate epic_id
            if task_data.epic_id and task_data.epic_id in invalid_epic_ids:
                failed_items.append(BulkOperationError(
                    index=index,
                    error_code=BulkErrorCode.EPIC_NOT_FOUND,
                    error_message=f"Epic with ID {task_data.epic_id} not found in project {project_id}",
                    item_data=task_data.model_dump()
                ))
                continue
            
            # Create task
            task_dict = task_data.model_dump()
            task_dict["project_id"] = project_id
            
            db_task = models.Task(**task_dict)
            db.add(db_task)
            db.flush()  # Get the task ID without committing
            
            # Create initial status history (only for non-default status)
            if task_data.status != models.TaskStatus.TODO:
                initial_history = models.StatusHistory(
                    task_id=db_task.id,
                    old_status=models.TaskStatus.TODO,
                    new_status=task_data.status
                )
                db.add(initial_history)
            
            # Refresh to get relationships
            db.refresh(db_task)
            successful_tasks.append(db_task)
            
        except SQLAlchemyError as e:
            failed_items.append(BulkOperationError(
                index=index,
                error_code=BulkErrorCode.DATABASE_ERROR,
                error_message=f"Database error: {str(e)}",
                item_data=task_data.model_dump()
            ))
    
    # Commit all successful operations
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to commit bulk task creation: {str(e)}")
    
    # Refresh all successful tasks to get complete data with batch loading
    if successful_tasks:
        task_ids = [task.id for task in successful_tasks]
        # Reload with relationships in a single query
        refreshed_tasks = db.query(models.Task).filter(
            models.Task.id.in_(task_ids)
        ).options(
            joinedload(models.Task.messages),
            joinedload(models.Task.status_history)
        ).all()
        successful_tasks = refreshed_tasks
    
    return BulkTaskResult(
        successful_tasks=successful_tasks,
        failed_items=failed_items,
        total_requested=len(bulk_request.tasks),
        total_successful=len(successful_tasks),
        total_failed=len(failed_items),
        operation_type=BulkOperationType.CREATE
    )

@router.put("/tasks/bulk", response_model=BulkTaskResult)
def bulk_update_tasks(
    bulk_request: BulkTaskUpdate,
    project_id: int = Path(..., description="The NUMERIC ID of the project"),
    db: Session = Depends(get_db)
):
    """
    Update multiple tasks in a single request.
    
    Features:
    - Validates all task IDs exist before updating any
    - Tracks status changes with history entries
    - Validates epic_ids if being updated
    - Returns detailed success/failure information
    """
    
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    
    successful_tasks = []
    failed_items = []
    
    # Pre-fetch all tasks to validate they exist and belong to project
    task_ids = [update.id for update in bulk_request.updates]
    existing_tasks = {
        task.id: task for task in 
        db.query(models.Task).filter(
            models.Task.id.in_(task_ids),
            models.Task.project_id == project_id
        ).all()
    }
    
    # Pre-validate epic_ids
    epic_ids = {
        update.update.epic_id for update in bulk_request.updates 
        if update.update.epic_id is not None
    }
    if epic_ids:
        valid_epics = set(
            db.query(models.Epic.id)
            .filter(models.Epic.id.in_(epic_ids), models.Epic.project_id == project_id)
            .all()
        )
        valid_epic_ids = {epic[0] for epic in valid_epics}
        invalid_epic_ids = epic_ids - valid_epic_ids
    else:
        invalid_epic_ids = set()
    
    # Process each update
    for index, update_item in enumerate(bulk_request.updates):
        try:
            task_id = update_item.id
            update_data = update_item.update
            
            # Check if task exists
            if task_id not in existing_tasks:
                failed_items.append(BulkOperationError(
                    index=index,
                    item_id=task_id,
                    error_code=BulkErrorCode.TASK_NOT_FOUND,
                    error_message=f"Task with ID {task_id} not found in project {project_id}",
                    item_data=update_item.model_dump()
                ))
                continue
            
            # Validate epic_id if being updated
            if update_data.epic_id and update_data.epic_id in invalid_epic_ids:
                failed_items.append(BulkOperationError(
                    index=index,
                    item_id=task_id,
                    error_code=BulkErrorCode.EPIC_NOT_FOUND,
                    error_message=f"Epic with ID {update_data.epic_id} not found in project {project_id}",
                    item_data=update_item.model_dump()
                ))
                continue
            
            # Apply updates
            db_task = existing_tasks[task_id]
            old_status = db_task.status
            
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(db_task, key, value)
            
            # Track status changes
            if 'status' in update_dict and update_dict['status'] != old_status:
                status_change = models.StatusHistory(
                    task_id=task_id,
                    old_status=old_status,
                    new_status=update_dict['status']
                )
                db.add(status_change)
            
            successful_tasks.append(db_task)
            
        except SQLAlchemyError as e:
            failed_items.append(BulkOperationError(
                index=index,
                item_id=update_item.id,
                error_code=BulkErrorCode.DATABASE_ERROR,
                error_message=f"Database error: {str(e)}",
                item_data=update_item.model_dump()
            ))
    
    # Commit all successful operations
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to commit bulk task updates: {str(e)}")
    
    # Refresh all successful tasks with batch loading
    if successful_tasks:
        task_ids = [task.id for task in successful_tasks]
        # Reload with relationships in a single query
        refreshed_tasks = db.query(models.Task).filter(
            models.Task.id.in_(task_ids)
        ).options(
            joinedload(models.Task.messages),
            joinedload(models.Task.status_history)
        ).all()
        successful_tasks = refreshed_tasks
    
    return BulkTaskResult(
        successful_tasks=successful_tasks,
        failed_items=failed_items,
        total_requested=len(bulk_request.updates),
        total_successful=len(successful_tasks),
        total_failed=len(failed_items),
        operation_type=BulkOperationType.UPDATE
    )

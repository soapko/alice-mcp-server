"""
Bulk decision operations router for Alice MCP server.
Provides endpoints for creating and updating multiple decisions in single API calls.
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from .. import models
from ..database import get_db
from ..schemas_bulk import (
    BulkDecisionCreate, BulkDecisionUpdate, BulkDecisionResult,
    BulkOperationError, BulkErrorCode, BulkOperationType
)

router = APIRouter(
    prefix="/{project_id}",
    tags=["bulk-decisions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/decisions/bulk", response_model=BulkDecisionResult)
def bulk_create_decisions(
    bulk_request: BulkDecisionCreate,
    project_id: int = Path(..., description="The NUMERIC ID of the project"),
    db: Session = Depends(get_db)
):
    """
    Create multiple decisions in a single request.
    
    Features:
    - Validates all decisions before creating any
    - Returns detailed success/failure information
    """
    
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    
    successful_decisions = []
    failed_items = []
    
    # Process each decision
    for index, decision_data in enumerate(bulk_request.decisions):
        try:
            # Validate task_id if provided
            if decision_data.task_id is not None:
                db_task = db.query(models.Task).filter(
                    models.Task.id == decision_data.task_id,
                    models.Task.project_id == project_id
                ).first()
                if not db_task:
                    failed_items.append(BulkOperationError(
                        index=index,
                        error_code=BulkErrorCode.TASK_NOT_FOUND,
                        error_message=f"Task with ID {decision_data.task_id} not found in project {project_id}",
                        item_data=decision_data.model_dump()
                    ))
                    continue
            
            # Create decision
            decision_dict = decision_data.model_dump()
            decision_dict["project_id"] = project_id
            
            db_decision = models.Decision(**decision_dict)
            db.add(db_decision)
            db.flush()  # Get the decision ID without committing
            
            # Refresh to get complete data
            db.refresh(db_decision)
            successful_decisions.append(db_decision)
            
        except SQLAlchemyError as e:
            failed_items.append(BulkOperationError(
                index=index,
                error_code=BulkErrorCode.DATABASE_ERROR,
                error_message=f"Database error: {str(e)}",
                item_data=decision_data.model_dump()
            ))
    
    # Commit all successful operations
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to commit bulk decision creation: {str(e)}")
    
    return BulkDecisionResult(
        successful_decisions=successful_decisions,
        failed_items=failed_items,
        total_requested=len(bulk_request.decisions),
        total_successful=len(successful_decisions),
        total_failed=len(failed_items),
        operation_type=BulkOperationType.CREATE
    )

@router.put("/decisions/bulk", response_model=BulkDecisionResult)
def bulk_update_decisions(
    bulk_request: BulkDecisionUpdate,
    project_id: int = Path(..., description="The NUMERIC ID of the project"),
    db: Session = Depends(get_db)
):
    """
    Update multiple decisions in a single request.
    
    Features:
    - Validates all decision IDs exist before updating any
    - Returns detailed success/failure information
    """
    
    # Verify project exists
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    
    successful_decisions = []
    failed_items = []
    
    # Pre-fetch all decisions to validate they exist and belong to project
    decision_ids = [update.id for update in bulk_request.updates]
    existing_decisions = {
        decision.id: decision for decision in 
        db.query(models.Decision).filter(
            models.Decision.id.in_(decision_ids),
            models.Decision.project_id == project_id
        ).all()
    }
    
    # Process each update
    for index, update_item in enumerate(bulk_request.updates):
        try:
            decision_id = update_item.id
            update_data = update_item.update
            
            # Check if decision exists
            if decision_id not in existing_decisions:
                failed_items.append(BulkOperationError(
                    index=index,
                    item_id=decision_id,
                    error_code=BulkErrorCode.DECISION_NOT_FOUND,
                    error_message=f"Decision with ID {decision_id} not found in project {project_id}",
                    item_data=update_item.model_dump()
                ))
                continue
            
            # Apply updates
            db_decision = existing_decisions[decision_id]
            
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(db_decision, key, value)
            
            successful_decisions.append(db_decision)
            
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
        raise HTTPException(status_code=500, detail=f"Failed to commit bulk decision updates: {str(e)}")
    
    return BulkDecisionResult(
        successful_decisions=successful_decisions,
        failed_items=failed_items,
        total_requested=len(bulk_request.updates),
        total_successful=len(successful_decisions),
        total_failed=len(failed_items),
        operation_type=BulkOperationType.UPDATE
    )

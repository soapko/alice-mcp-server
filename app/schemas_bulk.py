"""
Bulk operation schemas for Alice MCP server.
Provides schemas for creating and updating multiple tasks and decisions in single API calls.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from .schemas import TaskCreate, TaskUpdate, DecisionCreate, DecisionUpdate, Task, Decision

class BulkOperationType(str, Enum):
    CREATE = "create"
    UPDATE = "update"

class BulkErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    EPIC_NOT_FOUND = "EPIC_NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    DECISION_NOT_FOUND = "DECISION_NOT_FOUND"
    DATABASE_ERROR = "DATABASE_ERROR"

# Bulk Task Schemas
class BulkTaskCreate(BaseModel):
    tasks: List[TaskCreate]

class TaskUpdateWithId(BaseModel):
    id: int
    update: TaskUpdate

class BulkTaskUpdate(BaseModel):
    updates: List[TaskUpdateWithId]

# Bulk Decision Schemas  
class BulkDecisionCreate(BaseModel):
    decisions: List[DecisionCreate]

class DecisionUpdateWithId(BaseModel):
    id: int
    update: DecisionUpdate

class BulkDecisionUpdate(BaseModel):
    updates: List[DecisionUpdateWithId]

# Error and Result Schemas
class BulkOperationError(BaseModel):
    index: int  # Position in original request array
    item_id: Optional[int] = None  # For updates
    error_code: BulkErrorCode
    error_message: str
    field_errors: Optional[Dict[str, List[str]]] = None  # Pydantic validation errors
    item_data: Dict[str, Any]  # Original item data for debugging

class BulkTaskResult(BaseModel):
    successful_tasks: List[Task]
    failed_items: List[BulkOperationError]
    total_requested: int
    total_successful: int
    total_failed: int
    operation_type: BulkOperationType

class BulkDecisionResult(BaseModel):
    successful_decisions: List[Decision]
    failed_items: List[BulkOperationError]
    total_requested: int
    total_successful: int
    total_failed: int
    operation_type: BulkOperationType

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, ForwardRef
from .models import TaskStatus, DecisionStatus

# Forward reference for Task in Epic and Project
TaskRef = ForwardRef('Task')
DecisionRef = ForwardRef('Decision')
TaskPriorityRef = ForwardRef('TaskPriority')
EpicRef = ForwardRef('Epic')

# Schemas for Projects
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    path: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime
    tasks: List[TaskRef] = []
    epics: List[EpicRef] = []
    decisions: List[DecisionRef] = []
    task_priorities: List[TaskPriorityRef] = []

    class Config:
        from_attributes = True

# Schema for basic project identification (ID and Name)
class ProjectIdentifier(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# Schemas for Messages
class MessageBase(BaseModel):
    author: str
    message: str

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int
    task_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Schemas for Status History
class StatusHistoryBase(BaseModel):
    old_status: TaskStatus
    new_status: TaskStatus

class StatusHistory(StatusHistoryBase):
    id: int
    task_id: int
    changed_at: datetime

    class Config:
        from_attributes = True

# Schemas for Epics
class EpicBase(BaseModel):
    title: str
    description: Optional[str] = None
    assignee: Optional[str] = None
    project_id: Optional[int] = None

class EpicCreate(EpicBase):
    status: TaskStatus = TaskStatus.TODO

class EpicUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    assignee: Optional[str] = None
    project_id: Optional[int] = None

class Epic(EpicBase):
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    tasks: List[TaskRef] = []
    # Don't include project to avoid circular references

    class Config:
        from_attributes = True

# Schemas for Tasks
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    assignee: Optional[str] = None
    epic_id: Optional[int] = None
    project_id: Optional[int] = None

class TaskCreate(TaskBase):
    status: TaskStatus = TaskStatus.TODO

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    assignee: Optional[str] = None
    epic_id: Optional[int] = None
    project_id: Optional[int] = None

class TaskCore(TaskBase):
    """Core Task schema without related collections (messages and status history)"""
    id: int
    status: TaskStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Task(TaskCore):
    """Full Task schema including related collections"""
    messages: List[Message] = []
    status_history: List[StatusHistory] = []
    # Remove the epic field to avoid circular references
    # We already have epic_id from TaskBase
    priority: Optional[TaskPriorityRef] = None

    class Config:
        from_attributes = True

# Schemas for Decisions
class DecisionBase(BaseModel):
    title: str
    context_md: Optional[str] = None
    decision_md: Optional[str] = None
    consequences_md: Optional[str] = None
    status: DecisionStatus = DecisionStatus.PROPOSED
    task_id: Optional[int] = None

class DecisionCreate(DecisionBase):
    pass

class DecisionUpdate(BaseModel):
    title: Optional[str] = None
    context_md: Optional[str] = None
    decision_md: Optional[str] = None
    consequences_md: Optional[str] = None
    status: Optional[DecisionStatus] = None

class Decision(DecisionBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schemas for Task Priorities (Project Plan)
class TaskPriorityBase(BaseModel):
    task_id: int
    position: int
    rationale: Optional[str] = None

class TaskPriorityCreate(TaskPriorityBase):
    pass

class TaskPriorityUpdate(BaseModel):
    position: Optional[int] = None
    rationale: Optional[str] = None

class TaskPriority(TaskPriorityBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True

class ProjectPlanEntry(BaseModel):
    task: Task
    rationale: Optional[str] = None
    position: int

class ProjectPlanUpdate(BaseModel):
    task_id: int
    rationale: Optional[str] = None

# Resolve forward references
Epic.update_forward_refs()
Project.update_forward_refs()
Task.update_forward_refs()

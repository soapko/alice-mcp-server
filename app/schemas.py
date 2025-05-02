from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, ForwardRef
from .models import TaskStatus

# Forward reference for Task in Epic and Project
TaskRef = ForwardRef('Task')
EpicRef = ForwardRef('Epic')

# Schemas for Projects
class ProjectBase(BaseModel):
    name: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime
    tasks: List[TaskRef] = []
    epics: List[EpicRef] = []

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

    class Config:
        from_attributes = True

# Resolve forward references
Epic.update_forward_refs()
Project.update_forward_refs()

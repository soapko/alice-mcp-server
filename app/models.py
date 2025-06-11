from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base

class Project(Base):
    """Project model to isolate tasks and epics by project"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    epics = relationship("Epic", back_populates="project")
    tasks = relationship("Task", back_populates="project")


class TaskStatus(str, enum.Enum):
    TODO = "To-Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    CANCELED = "Canceled"

class Epic(Base):
    __tablename__ = "epics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    assignee = Column(String, nullable=True)
    # Project relationship - required after migration
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Relationships
    tasks = relationship("Task", back_populates="epic")
    project = relationship("Project", back_populates="epics")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.TODO)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    assignee = Column(String, nullable=True)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=True)
    # Project relationship - required after migration
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    messages = relationship("Message", back_populates="task", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="task", cascade="all, delete-orphan")
    epic = relationship("Epic", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    author = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="messages")

class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    old_status = Column(SQLEnum(TaskStatus), nullable=False)
    new_status = Column(SQLEnum(TaskStatus), nullable=False)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("Task", back_populates="status_history")

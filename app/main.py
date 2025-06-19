import logging
from fastapi import FastAPI, Request, status, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import asyncio
from sse_starlette.sse import EventSourceResponse
from datetime import datetime
from starlette.responses import Response

from .database import engine, Base, SessionLocal
from .routers import tasks, messages, epics, projects, decisions, project_plans
from . import models, schemas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Alice - Local MCP Server",
    description="A lightweight, local server for agile task workflows.",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Include routers
app.include_router(projects.router)  # Add projects router first
app.include_router(tasks.router)
app.include_router(messages.router)
app.include_router(epics.router)
app.include_router(decisions.router)
app.include_router(project_plans.router)

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

@app.exception_handler(SQLAlchemyError)
async def db_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal database error occurred."},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected internal server error occurred."},
    )

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to Alice MCP Server"}

@app.get("/events")
async def events(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            # Send a heartbeat every 30 seconds
            yield {
                "event": "heartbeat",
                "id": str(datetime.now().timestamp()),
                "retry": 15000,  # Reconnection time in milliseconds
                "data": datetime.now().isoformat()
            }
            await asyncio.sleep(30)
    
    return EventSourceResponse(event_generator(), media_type="text/event-stream")

# TODO: Include routers for tasks and messages

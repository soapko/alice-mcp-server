# Alice MCP Server - Technical Requirements

This document outlines the technical requirements for the Alice MCP Server, a local task management backend designed for AI coding environments.

## 1. System Requirements

### 1.1 Runtime Environment
- **Python:** 3.8+
- **Database:** SQLite 3.x (for local deployment)
- **Operating System:** Windows, macOS, or Linux

### 1.2 Development Dependencies
- **Core Framework:** FastAPI
- **Database ORM:** SQLAlchemy (with Alembic for migrations)
- **Data Validation:** Pydantic
- **ASGI Server:** Uvicorn
- **Testing:** pytest
- **Code Formatting:** black, isort
- **Linting:** flake8
- *(See `requirements.txt` for specific versions)*

## 2. Database Schema

The database utilizes SQLite and consists of the following tables:

### 2.1 `projects` Table
Stores project definitions to enable data isolation.
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 `epics` Table
Stores high-level epics, linked to a project.
```sql
CREATE TABLE epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK (status IN ('To-Do', 'In Progress', 'Done', 'Canceled')) DEFAULT 'To-Do',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assignee TEXT,
    project_id INTEGER NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### 2.3 `tasks` Table
Stores individual tasks, linked to a project and optionally an epic.
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK (status IN ('To-Do', 'In Progress', 'Done', 'Canceled')) DEFAULT 'To-Do',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assignee TEXT,
    epic_id INTEGER,
    project_id INTEGER NOT NULL,
    FOREIGN KEY (epic_id) REFERENCES epics(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### 2.4 `messages` Table
Stores messages associated with tasks.
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    author TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);
```

### 2.5 `status_history` Table
Logs changes in task status. *(Note: API endpoints for this are not currently implemented)*
```sql
CREATE TABLE status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    old_status TEXT NOT NULL CHECK (old_status IN ('To-Do', 'In Progress', 'Done', 'Canceled')),
    new_status TEXT NOT NULL CHECK (new_status IN ('To-Do', 'In Progress', 'Done', 'Canceled')),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);
```

## 3. API Endpoints

The API follows REST principles and utilizes project IDs in the path for resource isolation.

### 3.1 Projects (`/projects`)
- `POST /`: Create a new project.
  - Request Body: `{ "name": "string" }`
  - Response: `schemas.Project`
- `GET /`: List all project names.
  - Query Params: `skip` (int, default 0), `limit` (int, default 100)
  - Response: `List[str]`
- `GET /{project_id}`: Get project details by ID.
  - Response: `schemas.Project`
- `GET /by-name/{project_name}`: Get project details by name.
  - Response: `schemas.Project`

### 3.2 Epics (`/{project_id}/epics`)
- `POST /`: Create an epic within the specified project.
  - Request Body: `schemas.EpicCreate`
  - Response: `schemas.Epic`
- `GET /`: List epics within the project.
  - Query Params: `skip`, `limit`, `status`, `assignee`, `created_after`, `created_before`
  - Response: `List[schemas.Epic]`
- `GET /{epic_id}`: Get a specific epic.
  - Response: `schemas.Epic`
- `PUT /{epic_id}`: Update an epic.
  - Request Body: `schemas.EpicUpdate`
  - Response: `schemas.Epic`
- `DELETE /{epic_id}`: Delete an epic.
  - Response: `{"ok": true}`
- `GET /{epic_id}/tasks`: Get all tasks associated with an epic.
  - Response: `List[schemas.Task]`

### 3.3 Tasks (`/{project_id}/tasks`)
- `POST /`: Create a task within the specified project.
  - Request Body: `schemas.TaskCreate`
  - Response: `schemas.Task`
- `GET /`: List tasks within the project.
  - Query Params: `skip`, `limit`, `status`, `assignee`, `epic_id`, `created_after`, `created_before`
  - Response: `List[schemas.Task]`
- `GET /{task_id}`: Get a specific task.
  - Response: `schemas.Task`
- `PUT /{task_id}`: Update a task.
  - Request Body: `schemas.TaskUpdate`
  - Response: `schemas.Task`
- `DELETE /{task_id}`: Delete a task.
  - Response: `{"ok": true}`
- `PUT /{task_id}/move/{target_project_id}`: Move a task to a different project.
  - Response: `schemas.Task` (updated task)

### 3.4 Messages (`/{project_id}/tasks/{task_id}/messages`)
- `POST /`: Add a message to the specified task.
  - Request Body: `schemas.MessageCreate`
  - Response: `schemas.Message`
- `GET /`: Get all messages for the specified task.
  - Response: `List[schemas.Message]`

## 4. Performance Requirements

- **API Response Time:** < 150ms for typical local requests.
- **Concurrent Requests:** Support at least 50 simultaneous connections locally.
- **Database Operations:** < 75ms for standard CRUD operations on indexed fields.
- **Memory Usage:** < 150MB RAM under normal load.

## 5. Security Requirements

- **Authentication:** None required for default local deployment.
- **Input Validation:** Strict validation using Pydantic for all API inputs.
- **SQL Injection:** Prevented through the use of SQLAlchemy ORM.
- **CORS:** Configured to allow all origins (`*`) for local development convenience.
- **Rate Limiting:** Not implemented by default.

## 6. Development Guidelines

### 6.1 Code Style & Quality
- Follow PEP 8 guidelines.
- Use `black` for formatting and `isort` for import sorting.
- Apply `flake8` for linting.
- Utilize Python type hints extensively.
- Document all public modules, classes, and functions using docstrings.

### 6.2 Error Handling
- Return appropriate HTTP status codes (e.g., 404, 422, 500).
- Provide clear, JSON-formatted error messages in the response body.
- Log errors with sufficient detail for debugging (using Python's `logging` module).
- Handle potential `SQLAlchemyError` exceptions gracefully.

### 6.3 Testing
- Write unit tests using `pytest` for core logic (models, utility functions).
- Implement integration tests for all API endpoints.
- Maintain a test coverage target of > 80%.
- Ensure tests run in an isolated environment (e.g., using a test database).

## 7. Deployment

### 7.1 Local Development
- Simple setup using `pip install -r requirements.txt`.
- Run server with hot reloading via `uvicorn app.main:app --reload`.
- Use a local SQLite database file (e.g., `./alice.db`).
- Default port: 8000.

### 7.2 Production Considerations (Optional)
- Support for environment variable configuration.
- Option to use a more robust database (e.g., PostgreSQL).
- Dockerfile for containerized deployment.
- Structured logging (e.g., JSON format).

## 8. Monitoring

### 8.1 Logging
- Log incoming requests and their responses (including status codes).
- Log errors and exceptions with stack traces.
- Implement configurable log levels (DEBUG, INFO, WARNING, ERROR).

### 8.2 Metrics (Optional)
- Track API endpoint latency.
- Monitor database query times.
- Report basic system metrics like memory usage.

## 9. Documentation

- **API Documentation:** Auto-generated via FastAPI (Swagger UI at `/docs`, ReDoc at `/redoc`).
- **Application Overview:** `docs/app_overview.md` detailing architecture, features, etc.
- **README:** `README.md` with setup, usage, and contribution guidelines.
- **Requirements:** This document (`REQUIREMENTS.md`).

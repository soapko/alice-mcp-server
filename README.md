# Alice MCP - Agile Task Management

**Alice** is a lightweight, local server designed to support agile task workflows within AI coding environments like those using the Model Context Protocol (MCP). It provides a backend for managing projects, tasks, epics, and messages locally on your machine, featuring project isolation to support multiple distinct software projects.

See the [Documentation](#documentation) section for links to detailed guides.

## Key Features

- **Project Management:** Create and manage distinct projects.
- **Task & Epic Tracking:** Organize work using tasks and group them into epics.
- **Message Logging:** Attach messages or notes to specific tasks.
- **Dynamic Project Planning:** Create and manage a prioritized backlog of tasks. Alice can always tell you what the next most important task is, ensuring development efforts are perfectly aligned with project goals.
- **Architectural Decision Records (ADR):** Document key architectural decisions, their context, and consequences, providing a durable and queryable history of your project's evolution.
- **Project Isolation:** All tasks, epics, and messages are scoped to a project.
- **Local Operation:** Runs entirely on your local machine using a simple SQLite database.
- **MCP Integration:** Designed to be used as a tool provider within an MCP environment.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url> # Replace with the actual URL
    cd alice-mcp-server
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    # Create the environment
    python -m venv venv

    # Activate it (Linux/macOS)
    source venv/bin/activate

    # Activate it (Windows)
    # venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Server

### Automatic Startup (MCP Integration)

When used with an MCP-compatible environment, Alice now starts automatically - both the FastAPI backend and the MCP server components launch together. This is handled by the `scripts/start-alice-servers.sh` wrapper script, which:

- Activates the Python environment
- Installs dependencies
- Starts the FastAPI server
- Starts the MCP server

### Manual Startup (Development)

If you need to run the server manually (for development or testing), you can:

1. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The server will be available at `http://127.0.0.1:8000`

2. For debugging issues, you can run the wrapper script directly:
   ```bash
   /bin/zsh scripts/start-alice-servers.sh --debug
   ```

## Getting Started

1.  **Start the server** (see above).
2.  **Create a project:** Send a `POST` request to `/projects/` with a unique project name.
    ```json
    { "name": "my-new-project" }
    ```
3.  **Identify your project:** For interacting with tasks, epics, and messages via the Alice MCP server tools, you will use the project's **name** (e.g., "my-new-project") as the `project_id` argument. The MCP server handles the translation to the internal numeric ID required by the API.
4.  **API Endpoints (Direct API Usage):** If interacting directly with the FastAPI backend (not through the MCP server), all subsequent operations for tasks, epics, and messages require the internal numeric `project_id` in the URL path (e.g., `/{numeric_project_id}/tasks/`). You can find this numeric ID by listing projects (`GET /projects/`) or getting by name (`GET /projects/by-name/my-new-project`).

## Project Isolation API Structure

Alice's FastAPI backend uses numeric project IDs in the URL path to ensure data isolation. However, when using the **Alice MCP server tools**, you should provide the project's **name (string)** as the `project_id` argument. The MCP server will resolve this to the correct numeric ID for the API.

Direct API examples:

-   **Project Management:** `/projects/` (e.g., `POST /projects/`, `GET /projects/{project_id}`)
-   **Tasks:** `/{numeric_project_id}/tasks/` (e.g., `POST /1/tasks/`, `GET /1/tasks/{task_id}`)
-   **Epics:** `/{numeric_project_id}/epics/` (e.g., `POST /1/epics/`, `GET /1/epics/{epic_id}`)
-   **Messages:** `/{numeric_project_id}/tasks/{task_id}/messages/` (e.g., `POST /1/tasks/5/messages/`)

*Replace `1` with the actual internal numeric `project_id` when using the API directly.*

## Powerful New Features

Alice has been upgraded with powerful new features to supercharge your development workflow, ensuring that context and priority are never lost between coding sessions.

### Dynamic Project Planning

Tired of project plans becoming stale in static documents? Alice introduces a dynamic, queryable project plan.

-   **Create a Prioritized Backlog:** Use the `update_priority_plan` tool to set the exact order of tasks to be worked on. You can provide a rationale for each task's priority, giving essential context to your future self or other agents.
-   **Always Know What's Next:** The `get_next_task` tool instantly returns the highest-priority task that isn't yet "Done" or "Canceled". This eliminates ambiguity and ensures focus is always on the most critical work.
-   **Live Status Updates:** The project plan is always up-to-date. As tasks are completed, the plan automatically reflects their new status, providing a real-time view of progress.

### Architectural Decision Records (ADR)

Capture the "why" behind your project's design with a structured, queryable log of architectural decisions.

-   **Document Key Decisions:** Use the `create_decision` tool to record the context, decision, and consequences of important architectural choices.
-   **Preserve Context:** New development threads can quickly get up to speed by reviewing past decisions, preventing the re-litigation of settled issues and ensuring consistency over time.
-   **Link to Tasks:** Associate decisions with the specific tasks that prompted them, creating a clear audit trail of your project's evolution.

These features transform Alice from a simple task tracker into an intelligent partner that actively manages project context and priority, making your development process more efficient, transparent, and powerful.

## Running Tests

Ensure you have the virtual environment activated and dependencies installed. Then run:

```bash
pytest
```

## API Documentation

While the server is running, you can access the interactive API documentation (provided by FastAPI) in your browser:

-   **Swagger UI:** `http://127.0.0.1:8000/docs`
-   **ReDoc:** `http://127.0.0.1:8000/redoc`

## Documentation

Detailed documentation can be found in the `docs/` directory:

-   **[Application Overview](docs/app_overview.md):** Covers architecture, features, and technical stack.
-   **[Technical Requirements](docs/requirements.md):** Detailed system, database, and API specifications.
-   **[LLM Integration Guide](docs/llm_integration_guide.md):** Recommendations for integrating Alice with LLM custom instructions.

## Contributing

Contributions are welcome! Please follow these guidelines:

-   Adhere to the coding style (PEP 8, `black`, `isort`).
-   Use type hints.
-   Document public functions and APIs.
-   Write unit tests for new features or bug fixes.
-   Ensure all tests and linters pass before submitting changes.
-   For significant changes, consider opening an issue first to discuss the approach.

---
Alice is certified by MCP Review. See its listing here: https://mcpreview.com/mcp-servers/soapko/alice-mcp-server

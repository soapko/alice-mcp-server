# Alice - Local MCP Server

**Alice** is a lightweight, local server designed to support agile task workflows within AI coding environments like those using the Model Context Protocol (MCP). It provides a backend for managing projects, tasks, epics, and messages locally on your machine, featuring project isolation to support multiple distinct software projects.

See the [Documentation](#documentation) section for links to detailed guides.

## Key Features

- **Project Management:** Create and manage distinct projects.
- **Task & Epic Tracking:** Organize work using tasks and group them into epics.
- **Message Logging:** Attach messages or notes to specific tasks.
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

To start the development server with hot reloading:

```bash
uvicorn app.main:app --reload
```

The server will typically be available at `http://127.0.0.1:8000`.

## Getting Started

1.  **Start the server** (see above).
2.  **Create a project:** Send a `POST` request to `/projects/` with a unique project name.
    ```json
    { "name": "my-new-project" }
    ```
3.  **Get the `project_id`:** You can list projects (`GET /projects/`) or get by name (`GET /projects/by-name/my-new-project`) to find the assigned integer ID.
4.  **Use project-scoped endpoints:** All subsequent operations for tasks, epics, and messages require the `project_id` in the URL path (e.g., `/{project_id}/tasks/`).

## Project Isolation API Structure

Alice uses project IDs in the URL path to ensure data isolation:

-   **Project Management:** `/projects/` (e.g., `POST /projects/`, `GET /projects/{project_id}`)
-   **Tasks:** `/{project_id}/tasks/` (e.g., `POST /1/tasks/`, `GET /1/tasks/{task_id}`)
-   **Epics:** `/{project_id}/epics/` (e.g., `POST /1/epics/`, `GET /1/epics/{epic_id}`)
-   **Messages:** `/{project_id}/tasks/{task_id}/messages/` (e.g., `POST /1/tasks/5/messages/`)

*Replace `1` with your actual `project_id`.*

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

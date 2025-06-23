# Alice MCP - Lightweight Agile Task Management

**Alice** is a lightweight, local task management system designed for AI coding environments using the Model Context Protocol (MCP). It provides comprehensive project management capabilities with bulk operations, dynamic planning, and architectural decision tracking - all running locally on your machine with complete project isolation.

Optimized for **Cline** and other AI coding assistants, Alice transforms how you manage development workflows with intelligent automation and comprehensive tracking.

See the [Documentation](#documentation) section for detailed guides and the [Quick Start for Cline](#quick-start-for-cline-users) for immediate setup.

## Key Features

### **🚀 Efficient Bulk Operations**
- **Bulk Task Management:** Create and update multiple tasks simultaneously (75% reduction in API calls)
- **Bulk Decision Records:** Batch process architectural decisions with rich markdown support
- **Atomic Operations:** All-or-nothing processing with comprehensive error reporting
- **Performance Optimized:** SQLAlchemy batch loading for maximum efficiency

### **📊 Intelligent Project Management**
- **Project Isolation:** All data scoped to specific projects with secure separation
- **Dynamic Project Planning:** AI-queryable prioritized backlogs that adapt to progress
- **Task & Epic Tracking:** Hierarchical organization with status history tracking
- **Message Logging:** Contextual notes and discussions tied to specific tasks

### **🏗️ Architectural Decision Records (ADR)**
- **Structured Decision Tracking:** Document context, decisions, and consequences
- **Markdown-Rich Content:** Full formatting support for complex technical documentation
- **Task Integration:** Link decisions to the tasks that prompted them
- **Queryable History:** Maintain institutional knowledge across development cycles

### **🔧 Developer Experience**
- **Cline-Optimized:** Seamless integration with automatic server management
- **Local-First:** Runs entirely on your machine using SQLite - no external dependencies
- **MCP Native:** Built specifically for Model Context Protocol environments
- **Comprehensive Testing:** 62 tests ensuring reliability and stability

## Quick Start for Cline Users

**The fastest way to get Alice running with Cline:**

1. **Clone and Setup:**
   ```bash
   git clone https://github.com/your-organization/alice-mcp.git
   cd alice-mcp
   python -m venv alice-env
   source alice-env/bin/activate  # On Windows: alice-env\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Automated MCP Setup:**
   ```bash
   ./scripts/setup-alice-mcp.sh
   ```
   This single command handles everything: creates the MCP server, installs dependencies, builds the TypeScript, and updates your Cline settings.

3. **Restart Cline** and test with:
   ```
   Use alice-mcp-server to create a project named "test-project"
   ```

That's it! Alice is now integrated with Cline and ready for efficient project management.

## Advanced Setup

For manual setup or customization:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-organization/alice-mcp.git
    cd alice-mcp
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    # Create the environment
    python -m venv alice-env

    # Activate it (Linux/macOS)
    source alice-env/bin/activate

    # Activate it (Windows)
    # alice-env\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

For detailed manual setup instructions, see [LLM Installation Guide](llms-install.md).

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

### Bulk Operations - Improved Efficiency

Alice's bulk operations deliver improved efficiency for development project management:

**Bulk Task Operations:**
-   **`bulk_create_tasks`:** Create multiple tasks in a single operation with comprehensive validation
-   **`bulk_update_tasks`:** Update multiple tasks simultaneously with atomic transaction guarantees

**Bulk Decision Operations:**
-   **`bulk_create_decisions`:** Batch process architectural decisions with rich markdown support
-   **`bulk_update_decisions`:** Update decision statuses and content across multiple records

**Performance Benefits:**
-   **75% reduction** in API calls compared to individual operations
-   **Atomic transactions** with rollback protection ensure data consistency
-   **Detailed reporting** shows success/failure status for each item
-   **SQLAlchemy optimization** with batch loading for maximum database efficiency

**Example Usage:**
```javascript
// Create 5 tasks simultaneously
bulk_create_tasks("my-project", [
  { title: "Setup authentication", assignee: "Backend Team" },
  { title: "Design user interface", assignee: "Frontend Team" },
  { title: "Configure CI/CD pipeline", assignee: "DevOps Team" },
  { title: "Write API documentation", assignee: "Documentation Team" },
  { title: "Implement rate limiting", status: "In Progress" }
])

// Update multiple tasks with status changes
bulk_update_tasks("my-project", [
  { id: 1, update: { status: "Done" }},
  { id: 2, update: { status: "In Progress", assignee: "New Team" }},
  { id: 3, update: { description: "Updated requirements" }}
])
```

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

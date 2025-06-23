# Alice MCP Integration Guide for LLMs

This guide provides recommended instructions for incorporating the Alice MCP task tracking system into your custom instructions for Large Language Models (LLMs) or AI coding assistants.

## Server Setup

The Alice MCP system consists of two components:

1. **FastAPI Backend**: Provides the database and API endpoints for task management.
2. **Node.js MCP Server**: Interfaces between the LLM and the FastAPI backend.

Both components now start automatically when the MCP system is initialized, so no manual server startup is required. The wrapper script `scripts/start-alice-servers.sh` handles:

- Activating the Python virtual environment
- Installing required dependencies
- Starting the FastAPI server
- Verifying server availability
- Starting the MCP server with proper environment configuration

If you encounter any issues with the automatic startup, you can run the script manually with debug mode:
```bash
/bin/zsh path/to/alice-mcp/scripts/start-alice-servers.sh --debug
```

You may need to set the MCP server path environment variable if the script cannot find it automatically:
```bash
export ALICE_MCP_SERVER_PATH=path/to/alice-mcp-server/build/index.js
/bin/zsh path/to/alice-mcp/scripts/start-alice-servers.sh --debug
```

## Core Principles

- **Task-Driven Workflow:** All significant coding or documentation work should be tracked as an Alice task.
- **Project Context:** Ensure the correct `project_id` is used for all operations within a specific project.
- **Clear Status:** Keep task statuses (`To-Do`, `In Progress`, `Done`, `Canceled`, `Blocked`) up-to-date.
- **Communication Log:** Use messages to record progress, decisions, or issues related to a task.

## Recommended Custom Instructions Template

You can adapt the following template for your LLM's custom instructions. This template uses descriptive actions rather than specific tool syntax to be more tool-agnostic.

```
## Alice MCP Integration

### Task Tracking Protocol
  1. Each session REQUIRES a project identifier to track tasks with Alice.
     • If beginning work on a new project, first use the Alice MCP server's `create_project` tool. Note the **project name** returned in the response.
     • For all subsequent Task and Epic operations (e.g., `create_task`, `list_tasks`, `get_epic`), use the project's **name (string)** as the `project_id` argument in the MCP tool call. The server handles the translation to the internal numeric ID.

  2. Break down complex tasks into smaller, trackable units:
     • Create tasks using Alice's `create_task` tool with the required `project_id` (the project's name/slug) and `title`.
     • For efficiency, use `bulk_create_tasks` when creating multiple related tasks simultaneously (75% fewer API calls).
     • Optional fields: `description`, `assignee`, `status`, `epic_id`.

  3. For every coding or significant documentation task, you MUST:
     • Create an Alice task *before* starting implementation.
     • Reference the Alice task ID in your work (e.g., comments, commit messages) using the format "[Alice #<id>]".
     • Update task status accurately as you progress (e.g., `To-Do` → `In Progress` → `Done`).

### Status & Work Management
  1. When working through tasks:
     • Focus on ONE task at a time.
     • Update the task status to "In Progress" when you begin working on it.
     • Add detailed progress messages or notes to the task using Alice's message capabilities.
     • Update the status to "Done" only when the task is fully completed, verified, and tested (if applicable).
     • Move to the next task only after completing the current one.

  2. For blocked work:
     • Update the task status to "Blocked".
     • Add a message clearly explaining the blocker.
     • If possible, create new sub-tasks or related tasks to address the blocker.

### Documentation Integration
  1. Always keep project documentation current:
     • Update the main `README.md` immediately if the project structure, setup, or core usage changes.
     • Ensure technical documentation in the `docs/` directory remains synchronized with the implementation.
     • Where relevant, link documentation sections or updates back to specific Alice task IDs.

### Critical Code Protection (Optional but Recommended)
  1. For code sections that are critical, sensitive, or prone to regressions:
     • Add a comment marker like "// ALICE-TASK-REQ: [Alice #<id>]" directly in the code, linking it to the relevant task.
     • Ensure any commits modifying these guarded blocks reference the corresponding Alice task ID.
```

## Adapting for Your Environment

- **Tool Syntax:** Replace descriptive actions (e.g., "Use the Alice MCP server to create...") with the specific tool invocation syntax used by your AI assistant (e.g., `use_mcp_tool`, `<tool_name>`, etc.).
- **Server Name:** Ensure the correct server name for your Alice MCP instance is used (often just "alice" if running locally via standard MCP setup).
- **Project ID Handling:** Define how the LLM should obtain and remember the project **name** (which serves as the string `project_id` for most MCP tool calls) for the current session or project context.

By integrating Alice task tracking into your LLM's workflow, you can maintain better organization, context, and history for your development projects.

#!/usr/bin/env node
/**
 * Alice MCP Server Template
 * 
 * This template implements a Model Context Protocol (MCP) server for Alice,
 * a lightweight agile task management system. It provides tools for managing
 * projects, tasks, epics, and messages.
 * 
 * The server connects to the Alice FastAPI backend running at the URL
 * specified by the ALICE_API_URL environment variable (default: http://127.0.0.1:8000).
 * 
 * This template reflects the updated approach where Task and Epic related tools
 * expect a string-based 'project_id' (project name or slug), and the server
 * handles the lookup to the internal numeric ID required by the API.
 * 
 * To use this template:
 * 1. Ensure Node.js and npm are installed
 * 2. Create a new MCP server project using npx @modelcontextprotocol/create-server
 * 3. Replace the generated src/index.ts with this template
 * 4. Install dependencies: npm install axios
 * 5. Build the server: npm run build
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

// Get Alice API URL from environment variable, default to localhost:8000
const ALICE_API_URL = process.env.ALICE_API_URL || 'http://127.0.0.1:8000';

// Define TaskStatus enum matching the Python enum in the FastAPI backend
enum TaskStatus {
  TODO = "To-Do",
  IN_PROGRESS = "In Progress",
  DONE = "Done",
  CANCELED = "Canceled",
}

enum DecisionStatus {
  PROPOSED = "Proposed",
  ACCEPTED = "Accepted",
  REJECTED = "Rejected",
  SUPERSEDED = "Superseded",
}

// --- Tool Input Validation Functions ---

// Project validation functions (These use numeric project_id as they interact with /projects/ directly)
const isValidListProjectsArgs = (args: any): args is { skip?: number; limit?: number } =>
  typeof args === 'object' && args !== null &&
  (args.skip === undefined || typeof args.skip === 'number') &&
  (args.limit === undefined || typeof args.limit === 'number');

const isValidGetProjectArgs = (args: any): args is { project_id: number } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'number';

const isValidCreateProjectArgs = (args: any): args is { name: string; path: string; description?: string } =>
  typeof args === 'object' && args !== null &&
  typeof args.name === 'string' &&
  typeof args.path === 'string' &&
  (args.description === undefined || typeof args.description === 'string');

const isValidUpdateProjectArgs = (args: any): args is { project_id: number; name?: string; path?: string; description?: string } =>
  typeof args === 'object' && args !== null &&
  typeof args.project_id === 'number' &&
  (args.name === undefined || typeof args.name === 'string') &&
  (args.path === undefined || typeof args.path === 'string') &&
  (args.description === undefined || typeof args.description === 'string');

// Task validation functions (These use string project_id)
const isValidCreateTaskArgs = (args: any): args is { title: string; description?: string; assignee?: string; status?: TaskStatus; epic_id?: number; project_id: string } => {
  return typeof args === 'object' && args !== null && 
  typeof args.title === 'string' &&
  typeof args.project_id === 'string' && // Changed to string
  (args.description === undefined || typeof args.description === 'string') &&
  (args.assignee === undefined || typeof args.assignee === 'string') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status)) &&
  (args.epic_id === undefined || typeof args.epic_id === 'number');
} 

const isValidListTasksArgs = (args: any): args is { skip?: number; limit?: number; status?: TaskStatus; assignee?: string; epic_id?: number; created_after?: string; created_before?: string; project_id: string } =>
  typeof args === 'object' && args !== null &&
  typeof args.project_id === 'string' && // Changed to string
  (args.skip === undefined || typeof args.skip === 'number') &&
  (args.limit === undefined || typeof args.limit === 'number') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status)) &&
  (args.assignee === undefined || typeof args.assignee === 'string') &&
  (args.epic_id === undefined || typeof args.epic_id === 'number') &&
  (args.created_after === undefined || typeof args.created_after === 'string') && 
  (args.created_before === undefined || typeof args.created_before === 'string');

const isValidGetTaskArgs = (args: any): args is { task_id: number; project_id: string } =>
  typeof args === 'object' && args !== null && 
  typeof args.task_id === 'number' &&
  typeof args.project_id === 'string'; // Changed to string

const isValidUpdateTaskArgs = (args: any): args is { task_id: number; title?: string; description?: string; status?: TaskStatus; assignee?: string; epic_id?: number; project_id: string } =>
  typeof args === 'object' && args !== null && 
  typeof args.task_id === 'number' &&
  typeof args.project_id === 'string' && // Changed to string
  (args.title === undefined || typeof args.title === 'string') &&
  (args.description === undefined || typeof args.description === 'string') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status)) &&
  (args.assignee === undefined || typeof args.assignee === 'string') &&
  (args.epic_id === undefined || typeof args.epic_id === 'number');

const isValidDeleteTaskArgs = (args: any): args is { task_id: number; project_id: string } =>
  typeof args === 'object' && args !== null && 
  typeof args.task_id === 'number' &&
  typeof args.project_id === 'string'; // Changed to string

// Message validation functions (depend on Task, so project_id is string)
const isValidAddMessageArgs = (args: any): args is { task_id: number; author: string; message: string; project_id: string } =>
  typeof args === 'object' && args !== null && 
  typeof args.task_id === 'number' &&
  typeof args.project_id === 'string' && // Changed to string
  typeof args.author === 'string' && 
  typeof args.message === 'string';

const isValidGetMessagesArgs = (args: any): args is { task_id: number; project_id: string } =>
  typeof args === 'object' && args !== null && 
  typeof args.task_id === 'number' &&
  typeof args.project_id === 'string'; // Changed to string

// Epic validation functions (These use string project_id)
const isValidCreateEpicArgs = (args: any): args is { title: string; description?: string; assignee?: string; status?: TaskStatus; project_id: string } =>
  typeof args === 'object' && args !== null && 
  typeof args.title === 'string' &&
  typeof args.project_id === 'string' && // Changed to string
  (args.description === undefined || typeof args.description === 'string') &&
  (args.assignee === undefined || typeof args.assignee === 'string') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status));

const isValidListEpicsArgs = (args: any): args is { skip?: number; limit?: number; status?: TaskStatus; assignee?: string; created_after?: string; created_before?: string; project_id: string } =>
  typeof args === 'object' && args !== null &&
  typeof args.project_id === 'string' && // Changed to string
  (args.skip === undefined || typeof args.skip === 'number') &&
  (args.limit === undefined || typeof args.limit === 'number') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status)) &&
  (args.assignee === undefined || typeof args.assignee === 'string') &&
  (args.created_after === undefined || typeof args.created_after === 'string') && 
  (args.created_before === undefined || typeof args.created_before === 'string');

const isValidGetEpicArgs = (args: any): args is { epic_id: number; project_id: string } =>
  typeof args === 'object' && args !== null && 
  typeof args.epic_id === 'number' &&
  typeof args.project_id === 'string'; // Changed to string

const isValidUpdateEpicArgs = (args: any): args is { epic_id: number; title?: string; description?: string; status?: TaskStatus; assignee?: string; project_id: string } =>
  typeof args === 'object' && args !== null && 
  typeof args.epic_id === 'number' &&
  typeof args.project_id === 'string' && // Changed to string
  (args.title === undefined || typeof args.title === 'string') &&
  (args.description === undefined || typeof args.description === 'string') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status)) &&
  (args.assignee === undefined || typeof args.assignee === 'string');

const isValidDeleteEpicArgs = (args: any): args is { epic_id: number; project_id: string } =>
  typeof args === 'object' && args !== null && 
  typeof args.epic_id === 'number' &&
  typeof args.project_id === 'string'; // Changed to string

const isValidGetEpicTasksArgs = (args: any): args is { epic_id: number; project_id: string } =>
  typeof args === 'object' && args !== null && 
  typeof args.epic_id === 'number' &&
  typeof args.project_id === 'string'; // Changed to string

// Validation functions for Project Plan
const isValidGetPriorityPlanArgs = (args: any): args is { project_id: string } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string';

const isValidUpdatePriorityPlanArgs = (args: any): args is { project_id: string; plan_updates: { task_id: number; rationale?: string }[] } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string' && Array.isArray(args.plan_updates);

const isValidGetNextTaskArgs = (args: any): args is { project_id: string } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string';

// Validation functions for Decisions
const isValidCreateDecisionArgs = (args: any): args is { project_id: string; title: string; context_md?: string; decision_md?: string; consequences_md?: string; task_id?: number } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string' && typeof args.title === 'string';

const isValidListDecisionsArgs = (args: any): args is { project_id: string; skip?: number; limit?: number } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string';

const isValidGetDecisionArgs = (args: any): args is { project_id: string; decision_id: number } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string' && typeof args.decision_id === 'number';

const isValidUpdateDecisionArgs = (args: any): args is { project_id: string; decision_id: number; title?: string; context_md?: string; decision_md?: string; consequences_md?: string; status?: DecisionStatus } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string' && typeof args.decision_id === 'number';

// Bulk operations validation functions
const isValidBulkCreateTasksArgs = (args: any): args is { project_id: string; tasks: any[] } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string' && Array.isArray(args.tasks);

const isValidBulkUpdateTasksArgs = (args: any): args is { project_id: string; updates: any[] } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string' && Array.isArray(args.updates);

const isValidBulkCreateDecisionsArgs = (args: any): args is { project_id: string; decisions: any[] } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string' && Array.isArray(args.decisions);

const isValidBulkUpdateDecisionsArgs = (args: any): args is { project_id: string; updates: any[] } =>
  typeof args === 'object' && args !== null && typeof args.project_id === 'string' && Array.isArray(args.updates);

/**
 * Main AliceMcpServer class
 */
class AliceMcpServer {
  private server: Server;
  private axiosInstance;

  constructor() {
    this.server = new Server(
      {
        name: 'alice-mcp-server', // Standard server name
        version: '0.1.0',
        description: 'An agile tool for tracking stories for development',
      },
      {
        capabilities: {
          resources: {}, 
          tools: {},
        },
      }
    );

    this.axiosInstance = axios.create({
      baseURL: ALICE_API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupToolHandlers();

    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  /**
   * Sets up the tool handlers for the MCP server
   */
  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        // Project tools (use numeric project_id for direct project manipulation)
        {
          name: 'list_projects',
          description: 'List projects from Alice',
          inputSchema: {
            type: 'object',
            properties: {
              skip: { type: 'number', description: 'Number of projects to skip', default: 0 },
              limit: { type: 'number', description: 'Maximum number of projects to return', default: 100 },
            },
          },
        },
        {
          name: 'get_project',
          description: 'Get a specific project by ID from Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'number', description: 'Numeric ID of the project to retrieve' },
            },
            required: ['project_id'],
          },
        },
        {
          name: 'create_project',
          description: 'Create a new project in Alice',
          inputSchema: {
            type: 'object',
            properties: {
              name: { type: 'string', description: 'Name of the project' },
              path: { type: 'string', description: 'Working directory path for the project' },
              description: { type: 'string', description: 'Optional description of the project' },
            },
            required: ['name', 'path'],
          },
        },
        {
          name: 'update_project',
          description: 'Update an existing project in Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'number', description: 'Numeric ID of the project to update' },
              name: { type: 'string', description: 'New name for the project' },
              path: { type: 'string', description: 'New working directory path for the project' },
              description: { type: 'string', description: 'New description for the project' },
            },
            required: ['project_id'],
          },
        },

        // Task tools (use string project_id - name/slug)
        {
          name: 'create_task',
          description: 'Create a new task in Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) to create the task in" },
              title: { type: 'string', description: 'Title of the task' },
              description: { type: 'string', description: 'Optional description of the task' },
              assignee: { type: 'string', description: 'Optional assignee for the task' },
              status: { type: 'string', enum: Object.values(TaskStatus), description: 'Optional initial status (default: To-Do)' },
              epic_id: { type: 'number', description: 'Optional ID of the epic to associate this task with' },
            },
            required: ['project_id', 'title'],
          },
        },
        {
          name: 'list_tasks',
          description: 'List tasks from Alice with optional filters',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) to list tasks from" },
              skip: { type: 'number', description: 'Number of tasks to skip', default: 0 },
              limit: { type: 'number', description: 'Maximum number of tasks to return', default: 100 },
              status: { type: 'string', enum: Object.values(TaskStatus), description: 'Filter by task status' },
              assignee: { type: 'string', description: 'Filter by assignee' },
              epic_id: { type: 'number', description: 'Filter by epic ID' },
              created_after: { type: 'string', format: 'date-time', description: 'Filter tasks created after this timestamp (ISO 8601)' },
              created_before: { type: 'string', format: 'date-time', description: 'Filter tasks created before this timestamp (ISO 8601)' },
            },
            required: ['project_id'],
          },
        },
        {
          name: 'get_task',
          description: 'Get a specific task by ID from Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) the task belongs to" },
              task_id: { type: 'number', description: 'ID of the task to retrieve' },
            },
            required: ['project_id', 'task_id'],
          },
        },
        {
          name: 'update_task',
          description: 'Update an existing task in Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) the task belongs to" },
              task_id: { type: 'number', description: 'ID of the task to update' },
              title: { type: 'string', description: 'New title for the task' },
              description: { type: 'string', description: 'New description for the task' },
              status: { type: 'string', enum: Object.values(TaskStatus), description: 'New status for the task' },
              assignee: { type: 'string', description: 'New assignee for the task' },
              epic_id: { type: 'number', description: 'New epic ID for the task (set to null to remove from epic)' },
            },
            required: ['project_id', 'task_id'],
          },
        },
        {
          name: 'delete_task',
          description: 'Delete a task by ID from Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) the task belongs to" },
              task_id: { type: 'number', description: 'ID of the task to delete' },
            },
            required: ['project_id', 'task_id'],
          },
        },
        {
          name: 'add_message',
          description: 'Add a message to a specific task in Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) the task belongs to" },
              task_id: { type: 'number', description: 'ID of the task to add the message to' },
              author: { type: 'string', description: 'Author of the message' },
              message: { type: 'string', description: 'Content of the message' },
            },
            required: ['project_id', 'task_id', 'author', 'message'],
          },
        },
        {
          name: 'get_messages',
          description: 'Get all messages for a specific task from Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) the task belongs to" },
              task_id: { type: 'number', description: 'ID of the task to retrieve messages for' },
            },
            required: ['project_id', 'task_id'],
          },
        },

        // Epic tools (use string project_id - name/slug)
        {
          name: 'create_epic',
          description: 'Create a new epic in Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) to create the epic in" },
              title: { type: 'string', description: 'Title of the epic' },
              description: { type: 'string', description: 'Optional description of the epic' },
              assignee: { type: 'string', description: 'Optional assignee for the epic' },
              status: { type: 'string', enum: Object.values(TaskStatus), description: 'Optional initial status (default: To-Do)' },
            },
            required: ['project_id', 'title'],
          },
        },
        {
          name: 'list_epics',
          description: 'List epics from Alice with optional filters',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) to list epics from" },
              skip: { type: 'number', description: 'Number of epics to skip', default: 0 },
              limit: { type: 'number', description: 'Maximum number of epics to return', default: 100 },
              status: { type: 'string', enum: Object.values(TaskStatus), description: 'Filter by epic status' },
              assignee: { type: 'string', description: 'Filter by assignee' },
              created_after: { type: 'string', format: 'date-time', description: 'Filter epics created after this timestamp (ISO 8601)' },
              created_before: { type: 'string', format: 'date-time', description: 'Filter epics created before this timestamp (ISO 8601)' },
            },
            required: ['project_id'],
          },
        },
        {
          name: 'get_epic',
          description: 'Get a specific epic by ID from Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) the epic belongs to" },
              epic_id: { type: 'number', description: 'ID of the epic to retrieve' },
            },
            required: ['project_id', 'epic_id'],
          },
        },
        {
          name: 'update_epic',
          description: 'Update an existing epic in Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) the epic belongs to" },
              epic_id: { type: 'number', description: 'ID of the epic to update' },
              title: { type: 'string', description: 'New title for the epic' },
              description: { type: 'string', description: 'New description for the epic' },
              status: { type: 'string', enum: Object.values(TaskStatus), description: 'New status for the epic' },
              assignee: { type: 'string', description: 'New assignee for the epic' },
            },
            required: ['project_id', 'epic_id'],
          },
        },
        {
          name: 'delete_epic',
          description: 'Delete an epic by ID from Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) the epic belongs to" },
              epic_id: { type: 'number', description: 'ID of the epic to delete' },
            },
            required: ['project_id', 'epic_id'],
          },
        },
        {
          name: 'get_epic_tasks',
          description: 'Get all tasks for a specific epic from Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug (string identifier) the epic belongs to" },
              epic_id: { type: 'number', description: 'ID of the epic to retrieve tasks for' },
            },
            required: ['project_id', 'epic_id'],
          },
        },
        // Project Plan tools
        {
          name: 'get_priority_plan',
          description: 'Get the prioritized project plan',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
            },
            required: ['project_id'],
          },
        },
        {
          name: 'update_priority_plan',
          description: 'Update the prioritized project plan',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
              plan_updates: { 
                type: 'array', 
                items: {
                  type: 'object',
                  properties: {
                    task_id: { type: 'number' },
                    rationale: { type: 'string' },
                  },
                  required: ['task_id'],
                },
              },
            },
            required: ['project_id', 'plan_updates'],
          },
        },
        {
          name: 'get_next_task',
          description: 'Get the next actionable task from the project plan',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
            },
            required: ['project_id'],
          },
        },
        // Decision tools
        {
          name: 'create_decision',
          description: 'Create a new decision record',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
              title: { type: 'string' },
              context_md: { type: 'string' },
              decision_md: { type: 'string' },
              consequences_md: { type: 'string' },
              task_id: { type: 'number' },
            },
            required: ['project_id', 'title'],
          },
        },
        {
          name: 'list_decisions',
          description: 'List all decisions for a project',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
              skip: { type: 'number' },
              limit: { type: 'number' },
            },
            required: ['project_id'],
          },
        },
        {
          name: 'get_decision',
          description: 'Get a specific decision by ID',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
              decision_id: { type: 'number' },
            },
            required: ['project_id', 'decision_id'],
          },
        },
        {
          name: 'update_decision',
          description: 'Update an existing decision',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
              decision_id: { type: 'number' },
              title: { type: 'string' },
              context_md: { type: 'string' },
              decision_md: { type: 'string' },
              consequences_md: { type: 'string' },
              status: { type: 'string', enum: Object.values(DecisionStatus) },
            },
            required: ['project_id', 'decision_id'],
          },
        },

        // Bulk operation tools
        {
          name: 'bulk_create_tasks',
          description: 'Create multiple tasks in a single request',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
              tasks: {
                type: 'array',
                description: 'Array of task objects to create',
                items: {
                  type: 'object',
                  properties: {
                    title: { type: 'string', description: 'Title of the task' },
                    description: { type: 'string', description: 'Optional description of the task' },
                    assignee: { type: 'string', description: 'Optional assignee for the task' },
                    status: { type: 'string', enum: Object.values(TaskStatus), description: 'Optional initial status (default: To-Do)' },
                    epic_id: { type: 'number', description: 'Optional ID of the epic to associate this task with' },
                  },
                  required: ['title'],
                },
              },
            },
            required: ['project_id', 'tasks'],
          },
        },
        {
          name: 'bulk_update_tasks',
          description: 'Update multiple tasks in a single request',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
              updates: {
                type: 'array',
                description: 'Array of task update objects',
                items: {
                  type: 'object',
                  properties: {
                    id: { type: 'number', description: 'ID of the task to update' },
                    update: {
                      type: 'object',
                      properties: {
                        title: { type: 'string', description: 'New title for the task' },
                        description: { type: 'string', description: 'New description for the task' },
                        status: { type: 'string', enum: Object.values(TaskStatus), description: 'New status for the task' },
                        assignee: { type: 'string', description: 'New assignee for the task' },
                        epic_id: { type: 'number', description: 'New epic ID for the task' },
                      },
                    },
                  },
                  required: ['id', 'update'],
                },
              },
            },
            required: ['project_id', 'updates'],
          },
        },
        {
          name: 'bulk_create_decisions',
          description: 'Create multiple decisions in a single request',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
              decisions: {
                type: 'array',
                description: 'Array of decision objects to create',
                items: {
                  type: 'object',
                  properties: {
                    title: { type: 'string', description: 'Title of the decision' },
                    context_md: { type: 'string', description: 'Context of the decision in markdown' },
                    decision_md: { type: 'string', description: 'The decision in markdown' },
                    consequences_md: { type: 'string', description: 'Consequences of the decision in markdown' },
                    task_id: { type: 'number', description: 'Optional ID of the task this decision relates to' },
                  },
                  required: ['title'],
                },
              },
            },
            required: ['project_id', 'decisions'],
          },
        },
        {
          name: 'bulk_update_decisions',
          description: 'Update multiple decisions in a single request',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'string', description: "The project's name or slug" },
              updates: {
                type: 'array',
                description: 'Array of decision update objects',
                items: {
                  type: 'object',
                  properties: {
                    id: { type: 'number', description: 'ID of the decision to update' },
                    update: {
                      type: 'object',
                      properties: {
                        title: { type: 'string', description: 'New title for the decision' },
                        context_md: { type: 'string', description: 'New context in markdown' },
                        decision_md: { type: 'string', description: 'New decision in markdown' },
                        consequences_md: { type: 'string', description: 'New consequences in markdown' },
                        status: { type: 'string', enum: Object.values(DecisionStatus), description: 'New status for the decision' },
                      },
                    },
                  },
                  required: ['id', 'update'],
                },
              },
            },
            required: ['project_id', 'updates'],
          },
        },
      ],
    }));

    /**
     * Handles tool calls from the MCP client
     */
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      const args = request.params.arguments;

      try {
        let response; // To store API response
        // Helper function to resolve project name to numeric ID for relevant tools
        const resolveProjectId = async (projectName: string): Promise<number> => {
          try {
            const projectDetailsResponse = await this.axiosInstance.get(`/projects/by-name/${projectName}`);
            if (projectDetailsResponse.data && typeof projectDetailsResponse.data.id === 'number') {
              return projectDetailsResponse.data.id;
            } else {
              throw new McpError(ErrorCode.InvalidParams, `Project with name "${projectName}" found but has no valid numeric internal ID.`);
            }
          } catch (apiError) {
            if (axios.isAxiosError(apiError) && apiError.response?.status === 404) {
              throw new McpError(ErrorCode.InvalidParams, `Project with name "${projectName}" not found.`);
            }
            console.error(`Failed to resolve project name "${projectName}":`, apiError);
            throw new McpError(ErrorCode.InternalError, `Failed to resolve project name "${projectName}".`);
          }
        };
        
        let numericProjectId: number; // To store resolved numeric ID

        switch (toolName) {
          // Project tools
          case 'list_projects':
            if (!isValidListProjectsArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for list_projects');
            const listProjectsParams = Object.fromEntries(Object.entries(args).filter(([_, v]) => v !== undefined));
            response = await this.axiosInstance.get('/projects/', { params: listProjectsParams });
            break;
          case 'get_project':
            if (!isValidGetProjectArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_project');
            response = await this.axiosInstance.get(`/projects/${args.project_id}`); // Uses numeric ID
            break;
          case 'create_project': {
            if (!isValidCreateProjectArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for create_project');
            const createProjectResponse = await this.axiosInstance.post('/projects/', args);
            const createdProject = createProjectResponse.data;
            return { // Custom response for create_project
              content: [{
                type: 'text',
                text: `Project "${createdProject.name}" created successfully with internal ID ${createdProject.id}.\nUse "${createdProject.name}" as the project_id for subsequent operations.\nDetails: ${JSON.stringify(createdProject, null, 2)}`
              }]
            };
          }
          case 'update_project': { 
            if (!isValidUpdateProjectArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for update_project');
            const { project_id, ...updateProjectData } = args; // project_id is numeric here
            response = await this.axiosInstance.put(`/projects/${project_id}`, updateProjectData);
            break;
          }

          // Task tools
          case 'create_task':
            if (!isValidCreateTaskArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for create_task');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: createTaskProjectStringId, ...createTaskData } = args;
            response = await this.axiosInstance.post(`/${numericProjectId}/tasks/`, createTaskData);
            break;
          case 'list_tasks': { 
            if (!isValidListTasksArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for list_tasks');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: listTasksProjectStringId, ...listTaskFilters } = args;
            const listParams = Object.fromEntries(Object.entries(listTaskFilters).filter(([_, v]) => v !== undefined));
            response = await this.axiosInstance.get(`/${numericProjectId}/tasks/`, { params: listParams });
            break;
          }
          case 'get_task': {
            if (!isValidGetTaskArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_task');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: getTaskProjectStringId, task_id: getTaskId } = args; 
            response = await this.axiosInstance.get(`/${numericProjectId}/tasks/${getTaskId}`);
            break;
          }
          case 'update_task': {
            if (!isValidUpdateTaskArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for update_task');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: updateTaskProjectStringId, task_id: updateTaskId, ...updateTaskData } = args; 
            response = await this.axiosInstance.put(`/${numericProjectId}/tasks/${updateTaskId}`, updateTaskData);
            break;
          }
          case 'delete_task': {
            if (!isValidDeleteTaskArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for delete_task');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: deleteTaskProjectStringId, task_id: deleteTaskId } = args; 
            await this.axiosInstance.delete(`/${numericProjectId}/tasks/${deleteTaskId}`);
            return { content: [{ type: 'text', text: `Task ${deleteTaskId} deleted successfully from project ${args.project_id}.` }] };
          }
          case 'add_message': {
            if (!isValidAddMessageArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for add_message');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: addMessageProjectStringId, task_id: addMessageTaskId, ...messageData } = args; 
            response = await this.axiosInstance.post(`/${numericProjectId}/tasks/${addMessageTaskId}/messages/`, messageData);
            break;
          }
          case 'get_messages': {
            if (!isValidGetMessagesArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_messages');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: getMessagesProjectStringId, task_id: getMessagesTaskId } = args; 
            response = await this.axiosInstance.get(`/${numericProjectId}/tasks/${getMessagesTaskId}/messages/`);
            break;
          }

          // Epic tools
          case 'create_epic': {
            if (!isValidCreateEpicArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for create_epic');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: createEpicProjectStringId, ...createEpicData } = args; 
            response = await this.axiosInstance.post(`/${numericProjectId}/epics/`, createEpicData);
            break;
          }
          case 'list_epics': {
            if (!isValidListEpicsArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for list_epics');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: listEpicsProjectStringId, ...listEpicsFilters } = args; 
            const listEpicsParams = Object.fromEntries(Object.entries(listEpicsFilters).filter(([_, v]) => v !== undefined));
            response = await this.axiosInstance.get(`/${numericProjectId}/epics/`, { params: listEpicsParams });
            break;
          }
          case 'get_epic': {
            if (!isValidGetEpicArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_epic');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: getEpicProjectStringId, epic_id: getEpicId } = args; 
            response = await this.axiosInstance.get(`/${numericProjectId}/epics/${getEpicId}`);
            break;
          }
          case 'update_epic': {
            if (!isValidUpdateEpicArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for update_epic');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: updateEpicProjectStringId, epic_id: updateEpicId, ...updateEpicData } = args; 
            response = await this.axiosInstance.put(`/${numericProjectId}/epics/${updateEpicId}`, updateEpicData);
            break;
          }
          case 'delete_epic': {
            if (!isValidDeleteEpicArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for delete_epic');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: deleteEpicProjectStringId, epic_id: deleteEpicId } = args; 
            await this.axiosInstance.delete(`/${numericProjectId}/epics/${deleteEpicId}`);
            return { content: [{ type: 'text', text: `Epic ${deleteEpicId} deleted successfully from project ${args.project_id}.` }] };
          }
          case 'get_epic_tasks': {
            if (!isValidGetEpicTasksArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_epic_tasks');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: getEpicTasksProjectStringId, epic_id: getEpicTasksId } = args; 
            response = await this.axiosInstance.get(`/${numericProjectId}/epics/${getEpicTasksId}/tasks`);
            break;
          }

          // Project Plan cases
          case 'get_priority_plan':
            if (!isValidGetPriorityPlanArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_priority_plan');
            numericProjectId = await resolveProjectId(args.project_id);
            response = await this.axiosInstance.get(`/${numericProjectId}/priority-plan/`);
            break;
          case 'update_priority_plan':
            if (!isValidUpdatePriorityPlanArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for update_priority_plan');
            numericProjectId = await resolveProjectId(args.project_id);
            response = await this.axiosInstance.put(`/${numericProjectId}/priority-plan/`, args.plan_updates);
            break;
          case 'get_next_task':
            if (!isValidGetNextTaskArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_next_task');
            numericProjectId = await resolveProjectId(args.project_id);
            response = await this.axiosInstance.get(`/${numericProjectId}/priority-plan/next-task`);
            break;

          // Decision cases
          case 'create_decision':
            if (!isValidCreateDecisionArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for create_decision');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: createDecisionProjectStringId, ...createDecisionData } = args;
            response = await this.axiosInstance.post(`/${numericProjectId}/decisions/`, createDecisionData);
            break;
          case 'list_decisions':
            if (!isValidListDecisionsArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for list_decisions');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: listDecisionsProjectStringId, ...listDecisionsFilters } = args;
            response = await this.axiosInstance.get(`/${numericProjectId}/decisions/`, { params: listDecisionsFilters });
            break;
          case 'get_decision':
            if (!isValidGetDecisionArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_decision');
            numericProjectId = await resolveProjectId(args.project_id);
            response = await this.axiosInstance.get(`/${numericProjectId}/decisions/${args.decision_id}`);
            break;
          case 'update_decision':
            if (!isValidUpdateDecisionArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for update_decision');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: updateDecisionProjectStringId, decision_id: updateDecisionId, ...updateDecisionData } = args;
            response = await this.axiosInstance.put(`/${numericProjectId}/decisions/${updateDecisionId}`, updateDecisionData);
            break;

          // Bulk operation cases
          case 'bulk_create_tasks':
            if (!isValidBulkCreateTasksArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for bulk_create_tasks');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: bulkCreateTasksProjectStringId, ...bulkCreateTasksData } = args;
            response = await this.axiosInstance.post(`/${numericProjectId}/tasks/bulk`, bulkCreateTasksData);
            break;
          case 'bulk_update_tasks':
            if (!isValidBulkUpdateTasksArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for bulk_update_tasks');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: bulkUpdateTasksProjectStringId, ...bulkUpdateTasksData } = args;
            response = await this.axiosInstance.put(`/${numericProjectId}/tasks/bulk`, bulkUpdateTasksData);
            break;
          case 'bulk_create_decisions':
            if (!isValidBulkCreateDecisionsArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for bulk_create_decisions');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: bulkCreateDecisionsProjectStringId, ...bulkCreateDecisionsData } = args;
            response = await this.axiosInstance.post(`/${numericProjectId}/decisions/bulk`, bulkCreateDecisionsData);
            break;
          case 'bulk_update_decisions':
            if (!isValidBulkUpdateDecisionsArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for bulk_update_decisions');
            numericProjectId = await resolveProjectId(args.project_id);
            const { project_id: bulkUpdateDecisionsProjectStringId, ...bulkUpdateDecisionsData } = args;
            response = await this.axiosInstance.put(`/${numericProjectId}/decisions/bulk`, bulkUpdateDecisionsData);
            break;

          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${toolName}`);
        }

        // Default response formatting
        return {
          content: [{ type: 'text', text: JSON.stringify(response.data, null, 2) }],
        };
      } catch (error) {
        let errorMessage = `Error calling tool ${toolName}`;
        let isError = true; // Assume it's an error unless specifically handled (like 404)
        if (axios.isAxiosError(error)) {
          errorMessage = `Alice API error (${error.response?.status}): ${error.response?.data?.detail || error.message}`;
          if (error.response?.status === 404) {
             // For 404s, we might not want to flag it as a critical MCP error, 
             // but rather as a "not found" which is a valid outcome.
             // The `isError` flag in MCP response can control this behavior.
             // For now, keeping it as an error to be explicit.
          }
        } else if (error instanceof McpError) {
           errorMessage = error.message;
        } else if (error instanceof Error) {
           errorMessage = error.message;
        }
        console.error(`Error in tool ${toolName}:`, error);
        return {
          content: [{ type: 'text', text: errorMessage }],
          isError: isError, 
        };
      }
    });
  }

  /**
   * Start the MCP server
   */
  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Alice MCP server running on stdio'); // Log to stderr so it doesn't interfere with MCP protocol on stdout
  }
}

/**
 * Create and run the server
 */
const server = new AliceMcpServer();
server.run().catch(console.error);

// Note: Before building and running this server, you need to install the required dependencies:
//
// npm install @modelcontextprotocol/sdk axios
// npm install --save-dev typescript @types/node
//
// The tsconfig.json should include:
// {
//   "compilerOptions": {
//     "target": "ES2020",
//     "module": "NodeNext",
//     "moduleResolution": "NodeNext",
//     "esModuleInterop": true,
//     "outDir": "./build",
//     "strict": true,
//     "resolveJsonModule": true
//   },
//   "include": ["src/**/*"]
// }
//
// Build the server with:
// npm run build

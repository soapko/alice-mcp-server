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

// --- Tool Input Validation Functions ---

// Project validation functions
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

// Task validation functions
const isValidCreateTaskArgs = (args: any): args is { title: string; description?: string; assignee?: string; status?: TaskStatus; epic_id?: number; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.title === 'string' &&
  typeof args.project_id === 'number' &&
  (args.description === undefined || typeof args.description === 'string') &&
  (args.assignee === undefined || typeof args.assignee === 'string') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status)) &&
  (args.epic_id === undefined || typeof args.epic_id === 'number');

const isValidListTasksArgs = (args: any): args is { skip?: number; limit?: number; status?: TaskStatus; assignee?: string; epic_id?: number; created_after?: string; created_before?: string; project_id: number } =>
  typeof args === 'object' && args !== null &&
  typeof args.project_id === 'number' &&
  (args.skip === undefined || typeof args.skip === 'number') &&
  (args.limit === undefined || typeof args.limit === 'number') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status)) &&
  (args.assignee === undefined || typeof args.assignee === 'string') &&
  (args.epic_id === undefined || typeof args.epic_id === 'number') &&
  (args.created_after === undefined || typeof args.created_after === 'string') && // Assuming ISO 8601 string
  (args.created_before === undefined || typeof args.created_before === 'string'); // Assuming ISO 8601 string

const isValidGetTaskArgs = (args: any): args is { task_id: number; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.task_id === 'number' &&
  typeof args.project_id === 'number';

const isValidUpdateTaskArgs = (args: any): args is { task_id: number; title?: string; description?: string; status?: TaskStatus; assignee?: string; epic_id?: number; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.task_id === 'number' &&
  typeof args.project_id === 'number' &&
  (args.title === undefined || typeof args.title === 'string') &&
  (args.description === undefined || typeof args.description === 'string') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status)) &&
  (args.assignee === undefined || typeof args.assignee === 'string') &&
  (args.epic_id === undefined || typeof args.epic_id === 'number');

const isValidDeleteTaskArgs = (args: any): args is { task_id: number; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.task_id === 'number' &&
  typeof args.project_id === 'number';

// Message validation functions
const isValidAddMessageArgs = (args: any): args is { task_id: number; author: string; message: string; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.task_id === 'number' &&
  typeof args.project_id === 'number' &&
  typeof args.author === 'string' && 
  typeof args.message === 'string';

const isValidGetMessagesArgs = (args: any): args is { task_id: number; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.task_id === 'number' &&
  typeof args.project_id === 'number';

// Epic validation functions
const isValidCreateEpicArgs = (args: any): args is { title: string; description?: string; assignee?: string; status?: TaskStatus; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.title === 'string' &&
  typeof args.project_id === 'number' &&
  (args.description === undefined || typeof args.description === 'string') &&
  (args.assignee === undefined || typeof args.assignee === 'string') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status));

const isValidListEpicsArgs = (args: any): args is { skip?: number; limit?: number; status?: TaskStatus; assignee?: string; created_after?: string; created_before?: string; project_id: number } =>
  typeof args === 'object' && args !== null &&
  typeof args.project_id === 'number' &&
  (args.skip === undefined || typeof args.skip === 'number') &&
  (args.limit === undefined || typeof args.limit === 'number') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status)) &&
  (args.assignee === undefined || typeof args.assignee === 'string') &&
  (args.created_after === undefined || typeof args.created_after === 'string') && // Assuming ISO 8601 string
  (args.created_before === undefined || typeof args.created_before === 'string'); // Assuming ISO 8601 string

const isValidGetEpicArgs = (args: any): args is { epic_id: number; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.epic_id === 'number' &&
  typeof args.project_id === 'number';

const isValidUpdateEpicArgs = (args: any): args is { epic_id: number; title?: string; description?: string; status?: TaskStatus; assignee?: string; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.epic_id === 'number' &&
  typeof args.project_id === 'number' &&
  (args.title === undefined || typeof args.title === 'string') &&
  (args.description === undefined || typeof args.description === 'string') &&
  (args.status === undefined || Object.values(TaskStatus).includes(args.status)) &&
  (args.assignee === undefined || typeof args.assignee === 'string');

const isValidDeleteEpicArgs = (args: any): args is { epic_id: number; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.epic_id === 'number' &&
  typeof args.project_id === 'number';

const isValidGetEpicTasksArgs = (args: any): args is { epic_id: number; project_id: number } =>
  typeof args === 'object' && args !== null && 
  typeof args.epic_id === 'number' &&
  typeof args.project_id === 'number';

/**
 * Main AliceMcpServer class
 * 
 * This class implements the MCP server for Alice. It:
 * 1. Creates a server instance
 * 2. Sets up handlers for the various tools
 * 3. Handles requests to call tools
 * 4. Manages communication with the FastAPI backend
 */
class AliceMcpServer {
  private server: Server;
  private axiosInstance;

  constructor() {
    // Initialize the MCP server
    this.server = new Server(
      {
        name: 'alice-mcp-server',
        version: '0.1.0',
        description: 'An agile tool for tracking stories for development',
      },
      {
        capabilities: {
          resources: {}, // No resources defined for now
          tools: {},
        },
      }
    );

    // Initialize the HTTP client for communicating with the FastAPI backend
    this.axiosInstance = axios.create({
      baseURL: ALICE_API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Set up the tool handlers
    this.setupToolHandlers();

    // Error handling
    this.server.onerror = (error) => console.error('[MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  /**
   * Sets up the tool handlers for the MCP server
   * 
   * This method defines all the tools that the MCP server provides
   * and their input schemas.
   */
  private setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        // Project tools
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
              project_id: { type: 'number', description: 'ID of the project to retrieve' },
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
              project_id: { type: 'number', description: 'ID of the project to update' },
              name: { type: 'string', description: 'New name for the project' },
              path: { type: 'string', description: 'New working directory path for the project' },
              description: { type: 'string', description: 'New description for the project' },
            },
            required: ['project_id'],
          },
        },

        // Task tools
        {
          name: 'create_task',
          description: 'Create a new task in Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'number', description: 'ID of the project to create the task in' },
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
              project_id: { type: 'number', description: 'ID of the project to list tasks from' },
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
              project_id: { type: 'number', description: 'ID of the project the task belongs to' },
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
              project_id: { type: 'number', description: 'ID of the project the task belongs to' },
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
              project_id: { type: 'number', description: 'ID of the project the task belongs to' },
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
              project_id: { type: 'number', description: 'ID of the project the task belongs to' },
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
              project_id: { type: 'number', description: 'ID of the project the task belongs to' },
              task_id: { type: 'number', description: 'ID of the task to retrieve messages for' },
            },
            required: ['project_id', 'task_id'],
          },
        },

        // Epic tools
        {
          name: 'create_epic',
          description: 'Create a new epic in Alice',
          inputSchema: {
            type: 'object',
            properties: {
              project_id: { type: 'number', description: 'ID of the project to create the epic in' },
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
              project_id: { type: 'number', description: 'ID of the project to list epics from' },
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
              project_id: { type: 'number', description: 'ID of the project the epic belongs to' },
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
              project_id: { type: 'number', description: 'ID of the project the epic belongs to' },
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
              project_id: { type: 'number', description: 'ID of the project the epic belongs to' },
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
              project_id: { type: 'number', description: 'ID of the project the epic belongs to' },
              epic_id: { type: 'number', description: 'ID of the epic to retrieve tasks for' },
            },
            required: ['project_id', 'epic_id'],
          },
        },
      ],
    }));

    /**
     * Handles tool calls from the MCP client
     * 
     * This method processes requests to call tools, validates arguments,
     * calls the appropriate API endpoint, and returns the results.
     */
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const toolName = request.params.name;
      const args = request.params.arguments;

      try {
        let response;
        switch (toolName) {
          // Project tools
          case 'list_projects':
            if (!isValidListProjectsArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for list_projects');
            const listProjectsParams = Object.fromEntries(Object.entries(args).filter(([_, v]) => v !== undefined));
            response = await this.axiosInstance.get('/projects/', { params: listProjectsParams });
            break;
          case 'get_project':
            if (!isValidGetProjectArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_project');
            response = await this.axiosInstance.get(`/projects/${args.project_id}`);
            break;
          case 'create_project':
            if (!isValidCreateProjectArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for create_project');
            response = await this.axiosInstance.post('/projects/', args);
            break;
          case 'update_project':
            if (!isValidUpdateProjectArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for update_project');
            const { project_id, ...updateProjectData } = args;
            response = await this.axiosInstance.put(`/projects/${project_id}`, updateProjectData);
            break;

          // Task tools
          case 'create_task':
            if (!isValidCreateTaskArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for create_task');
            const { project_id: createTaskProjectId, ...createTaskData } = args;
            response = await this.axiosInstance.post(`/${createTaskProjectId}/tasks/`, createTaskData);
            break;
          case 'list_tasks':
            if (!isValidListTasksArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for list_tasks');
            const { project_id: listTasksProjectId, ...listTaskFilters } = args;
            // Filter out undefined params before sending
            const listParams = Object.fromEntries(Object.entries(listTaskFilters).filter(([_, v]) => v !== undefined));
            response = await this.axiosInstance.get(`/${listTasksProjectId}/tasks/`, { params: listParams });
            break;
          case 'get_task':
            if (!isValidGetTaskArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_task');
            const { project_id: getTaskProjectId, task_id: getTaskId } = args;
            response = await this.axiosInstance.get(`/${getTaskProjectId}/tasks/${getTaskId}`);
            break;
          case 'update_task':
            if (!isValidUpdateTaskArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for update_task');
            const { project_id: updateTaskProjectId, task_id: updateTaskId, ...updateTaskData } = args;
            response = await this.axiosInstance.put(`/${updateTaskProjectId}/tasks/${updateTaskId}`, updateTaskData);
            break;
          case 'delete_task':
            if (!isValidDeleteTaskArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for delete_task');
            const { project_id: deleteTaskProjectId, task_id: deleteTaskId } = args;
            response = await this.axiosInstance.delete(`/${deleteTaskProjectId}/tasks/${deleteTaskId}`);
            // Delete returns 204 No Content, so create a success message
            return { content: [{ type: 'text', text: `Task ${deleteTaskId} deleted successfully.` }] };
          case 'add_message':
            if (!isValidAddMessageArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for add_message');
            const { project_id: addMessageProjectId, task_id: addMessageTaskId, ...messageData } = args;
            response = await this.axiosInstance.post(`/${addMessageProjectId}/tasks/${addMessageTaskId}/messages/`, messageData);
            break;
          case 'get_messages':
            if (!isValidGetMessagesArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_messages');
            const { project_id: getMessagesProjectId, task_id: getMessagesTaskId } = args;
            response = await this.axiosInstance.get(`/${getMessagesProjectId}/tasks/${getMessagesTaskId}/messages/`);
            break;

          // Epic tools
          case 'create_epic':
            if (!isValidCreateEpicArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for create_epic');
            const { project_id: createEpicProjectId, ...createEpicData } = args;
            response = await this.axiosInstance.post(`/${createEpicProjectId}/epics/`, createEpicData);
            break;
          case 'list_epics':
            if (!isValidListEpicsArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for list_epics');
            const { project_id: listEpicsProjectId, ...listEpicsFilters } = args;
            // Filter out undefined params before sending
            const listEpicsParams = Object.fromEntries(Object.entries(listEpicsFilters).filter(([_, v]) => v !== undefined));
            response = await this.axiosInstance.get(`/${listEpicsProjectId}/epics/`, { params: listEpicsParams });
            break;
          case 'get_epic':
            if (!isValidGetEpicArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_epic');
            const { project_id: getEpicProjectId, epic_id: getEpicId } = args;
            response = await this.axiosInstance.get(`/${getEpicProjectId}/epics/${getEpicId}`);
            break;
          case 'update_epic':
            if (!isValidUpdateEpicArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for update_epic');
            const { project_id: updateEpicProjectId, epic_id: updateEpicId, ...updateEpicData } = args;
            response = await this.axiosInstance.put(`/${updateEpicProjectId}/epics/${updateEpicId}`, updateEpicData);
            break;
          case 'delete_epic':
            if (!isValidDeleteEpicArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for delete_epic');
            const { project_id: deleteEpicProjectId, epic_id: deleteEpicId } = args;
            response = await this.axiosInstance.delete(`/${deleteEpicProjectId}/epics/${deleteEpicId}`);
            // Delete returns 204 No Content, so create a success message
            return { content: [{ type: 'text', text: `Epic ${deleteEpicId} deleted successfully.` }] };
          case 'get_epic_tasks':
            if (!isValidGetEpicTasksArgs(args)) throw new McpError(ErrorCode.InvalidParams, 'Invalid arguments for get_epic_tasks');
            const { project_id: getEpicTasksProjectId, epic_id: getEpicTasksId } = args;
            response = await this.axiosInstance.get(`/${getEpicTasksProjectId}/epics/${getEpicTasksId}/tasks`);
            break;

          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${toolName}`);
        }

        return {
          content: [{ type: 'text', text: JSON.stringify(response.data, null, 2) }],
        };
        } catch (error) {
          let errorMessage = `Error calling tool ${toolName}`;
          let isError = true;
          if (axios.isAxiosError(error)) {
            errorMessage = `Alice API error (${error.response?.status}): ${error.response?.data?.detail || error.message}`;
            // If Alice returns 404, treat it as a specific error, not a general server error
            if (error.response?.status === 404) {
               return { content: [{ type: 'text', text: errorMessage }], isError: false }; // Return as non-error for 404
            }
          } else if (error instanceof McpError) {
             errorMessage = error.message; // Use the specific MCP error message
          } else if (error instanceof Error) {
             errorMessage = error.message;
          }
          console.error(`Error in tool ${toolName}:`, error);
          // Return error details in the response
          return {
            content: [{ type: 'text', text: errorMessage }],
            isError: isError,
          };
        }
      }
    });
  }

  /**
   * Start the MCP server
   * 
   * This method connects to the transport and starts the server.
   */
  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Alice MCP server running on stdio');
  }
}

/**
 * Create and run the server
 * 
 * This is the entry point for the MCP server.
 */
const server = new AliceMcpServer();
server.run().catch(console.error);

/**
 * Note: Before building and running this server, you need to install the required dependencies:
 * 
 * npm install @modelcontextprotocol/sdk axios
 * npm install --save-dev typescript @types/node
 * 
 * The tsconfig.json should include:
 * {
 *   "compilerOptions": {
 *     "target": "ES2020",
 *     "module": "NodeNext",
 *     "moduleResolution": "NodeNext",
 *     "esModuleInterop": true,
 *     "outDir": "./build",
 *     "strict": true,
 *     "resolveJsonModule": true
 *   },
 *   "include": ["src/**/*"]
 * }
 * 
 * Build the server with:
 * npm run build
 */

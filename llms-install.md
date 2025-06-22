# Alice MCP Installation Guide for Cline

This comprehensive guide provides step-by-step instructions for installing and configuring the Alice MCP system for use with **Cline** or similar AI coding assistants. Alice delivers enterprise-grade project management with bulk operations, dynamic planning, and architectural decision tracking.

## What You're Installing

Alice is a powerful two-component system:

1. **FastAPI Backend**: Python-based REST API with SQLite database
   - Manages projects, tasks, epics, messages, and decisions
   - Includes 4 enterprise-grade bulk operation endpoints
   - 62 comprehensive tests ensuring reliability

2. **MCP Server**: TypeScript-based integration layer
   - Built from our custom template with all bulk operations
   - Seamless Cline integration with automatic server management
   - Project ID resolution and comprehensive error handling

## Prerequisites

- **Python 3.8+** installed on your system
- **Node.js 14+** installed on your system  
- **Git** for cloning the repository
- **Cline** desktop app installed

## Installation Methods

**Choose your installation approach:**

1. **🚀 Automated Setup** (Strongly Recommended): Single script handles everything
2. **🔧 Manual Installation**: Step-by-step configuration for customization

## 🚀 Automated Setup (Strongly Recommended)

**The fastest way to get Alice running with all bulk operations:**

### Step 1: Clone and Setup Backend

```bash
git clone https://github.com/your-organization/alice-mcp.git
cd alice-mcp

# Create and activate Python environment
python -m venv alice-env
source alice-env/bin/activate  # Windows: alice-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: One-Command MCP Setup

Our comprehensive setup script handles everything automatically:

```bash
# Make the script executable if needed
chmod +x scripts/setup-alice-mcp.sh

# Run the automated setup
./scripts/setup-alice-mcp.sh
```

**What this script does:**
1. ✅ Checks for Node.js and npm prerequisites
2. ✅ Creates MCP server at `~/Documents/Cline/MCP/alice-mcp-server`
3. ✅ Applies our comprehensive template with all 30+ tools including bulk operations
4. ✅ Installs TypeScript dependencies and builds the server
5. ✅ Updates your Cline MCP settings automatically
6. ✅ Provides verification steps

### Step 3: Test Your Installation

Restart Cline and test:
```
Use alice-mcp-server to create a project named "test-project"
```

That's it! You now have enterprise-grade Alice with all bulk operations ready.

### Advanced Setup Options

```bash
# Custom MCP server location
./scripts/setup-alice-mcp.sh -d /custom/path/to/mcp/server

# Verbose output for troubleshooting
./scripts/setup-alice-mcp.sh -v

# See all options
./scripts/setup-alice-mcp.sh -h
```

## 🔧 Manual Installation

For users who prefer step-by-step configuration or need customization:

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-organization/alice-mcp.git
cd alice-mcp
```

### Step 2: Setup the Python Environment

```bash
# Create a Python virtual environment
python -m venv alice-env

# Activate the virtual environment
# On macOS/Linux:
source alice-env/bin/activate
# On Windows:
# alice-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Set Up the MCP Server

#### Using the Setup Script (Recommended)

The Alice repository includes a setup script that automates the MCP server creation process:

```bash
# Make the script executable if needed
chmod +x scripts/setup-alice-mcp.sh

# Run the setup script
./scripts/setup-alice-mcp.sh
```

The script will:
1. Check for Node.js and npm
2. Create the MCP server in `~/Documents/Cline/MCP/alice-mcp-server`
3. Set up the TypeScript project with the Alice template
4. Install required dependencies
5. Build the server
6. Update the Cline MCP settings file
7. Provide clear next steps

For advanced options, run with `-h` flag:
```bash
./scripts/setup-alice-mcp.sh -h
```

#### Option B: Using Cline to Create the MCP Server

Alternatively, you can use Cline's AI capabilities to create the MCP server:

1. Open Cline and ask it to create an MCP server for Alice, sharing the template:
   ```
   Please create a TypeScript MCP server for Alice in the default location 
   (~/Documents/Cline/MCP/alice-mcp-server) that connects to a FastAPI 
   backend running at http://127.0.0.1:8000. Use the template from the
   alice-mcp repository at: templates/alice-mcp-template.ts
   ```

2. Cline will guide you through creating the TypeScript server based on the template, which implements tools for:
   - Managing projects
   - Creating and updating tasks
   - Managing epics
   - Adding messages to tasks

### Step 4: Configure the MCP Settings for Cline

> **Note:** If you used the setup script (Option A above), this step is already done for you. You can skip to Step 5.

1. Open the Cline MCP settings file located at:
   - macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
   - Windows: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

2. Add the Alice MCP server configuration to the `mcpServers` object in the settings file:

```json
{
  "mcpServers": {
    "alice-mcp-server": {
      "command": "node",
      "args": ["<PATH_TO_MCP_SERVER>/build/index.js"],
      "env": {
        "ALICE_API_URL": "http://127.0.0.1:8000"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Replace `<PATH_TO_MCP_SERVER>` with the path to the MCP server (typically `~/Documents/Cline/MCP/alice-mcp-server`).

Alternatively, if you prefer to use the wrapper script instead of directly calling the MCP server:

```json
{
  "mcpServers": {
    "alice-mcp-server": {
      "command": "/bin/zsh",
      "args": ["<PATH_TO_ALICE>/scripts/start-alice-servers.sh"],
      "env": {
        "ALICE_API_URL": "http://127.0.0.1:8000",
        "ALICE_MCP_SERVER_PATH": "<PATH_TO_MCP_SERVER>/build/index.js"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Where:
- `<PATH_TO_ALICE>` is the absolute path to your Alice repository
- `<PATH_TO_MCP_SERVER>` is the path to the MCP server

## Manual Installation

If you prefer to set up everything manually without the setup script:

### Steps 1-2: Same as above

### Step 3: Manually Create the MCP Server

1. Create the MCP server directory:
   ```bash
   mkdir -p ~/Documents/Cline/MCP/alice-mcp-server
   cd ~/Documents/Cline/MCP/alice-mcp-server
   ```

2. Initialize a Node.js project and install dependencies:
   ```bash
   npm init -y
   npm install @modelcontextprotocol/sdk axios
   npm install --save-dev typescript @types/node
   ```

3. Set up TypeScript configuration:
   ```bash
   cat > tsconfig.json << EOL
   {
     "compilerOptions": {
       "target": "ES2020",
       "module": "NodeNext",
       "moduleResolution": "NodeNext",
       "esModuleInterop": true,
       "outDir": "./build",
       "strict": true,
       "resolveJsonModule": true
     },
     "include": ["src/**/*"]
   }
   EOL
   ```

4. Create the source directory and copy the template file:
   ```bash
   mkdir -p src
   cp /path/to/alice-mcp/templates/alice-mcp-template.ts src/index.ts
   ```

5. Update package.json to add build script:
   ```bash
   # Add in package.json under "scripts":
   "build": "tsc && chmod +x build/index.js"
   ```

6. Build the TypeScript code:
   ```bash
   npm run build
   ```

### Step 4: Configure as in the Simplified Method

## Verifying the Installation

1. Restart Cline to load the updated MCP settings.

2. In a new Cline conversation, test the Alice MCP server by creating a project:
   ```
   Use the alice-mcp-server tool to create a project named "test-project" with 
   path "/path/to/your/project".
   ```

If the installation was successful, Cline should be able to access the Alice MCP tools and create the project.

## Using Alice in Your Workflow

### **🚀 Available Tools Overview**

Alice provides **30+ comprehensive tools** including:

**Project Management:**
- `create_project`, `list_projects`, `get_project`, `update_project`

**Individual Operations:**
- `create_task`, `list_tasks`, `get_task`, `update_task`, `delete_task`
- `create_epic`, `list_epics`, `get_epic`, `update_epic`, `delete_epic`
- `create_decision`, `list_decisions`, `get_decision`, `update_decision`
- `add_message`, `get_messages`

**🔥 NEW: Enterprise Bulk Operations:**
- `bulk_create_tasks` - Create multiple tasks simultaneously
- `bulk_update_tasks` - Update multiple tasks in one operation
- `bulk_create_decisions` - Batch process architectural decisions
- `bulk_update_decisions` - Update multiple decisions efficiently

**Dynamic Planning:**
- `get_priority_plan`, `update_priority_plan`, `get_next_task`

### **Basic Workflow:**

1. **Create a project:**
   ```
   Use alice-mcp-server to create a project named "your-project-name" 
   with path "/path/to/your/project"
   ```

2. **Use bulk operations for efficiency:**
   ```
   Use alice-mcp-server bulk_create_tasks to create multiple tasks for project "your-project-name":
   - Setup authentication system
   - Design user interface  
   - Implement API endpoints
   - Write comprehensive tests
   - Deploy to production
   ```

3. **Track architectural decisions:**
   ```
   Use alice-mcp-server bulk_create_decisions to document multiple architectural decisions 
   for project "your-project-name" with context, decisions, and consequences
   ```

### **Enterprise Bulk Operations Examples:**

**Bulk Task Creation (75% fewer API calls):**
```
Use alice-mcp-server bulk_create_tasks for project "my-project" with tasks:
[
  { title: "Setup CI/CD pipeline", assignee: "DevOps Team", status: "To-Do" },
  { title: "Implement authentication", assignee: "Backend Team", status: "In Progress" },
  { title: "Design UI mockups", assignee: "Design Team", status: "To-Do" }
]
```

**Bulk Status Updates:**
```
Use alice-mcp-server bulk_update_tasks for project "my-project":
[
  { id: 1, update: { status: "Done" }},
  { id: 2, update: { status: "In Progress", assignee: "New Team" }},
  { id: 3, update: { description: "Updated requirements based on feedback" }}
]
```

## Troubleshooting

### Server Not Starting

If the MCP server fails to start:

1. Check the paths in your MCP settings file
2. Try running the start script manually with debug flag:
   ```bash
   /bin/zsh /path/to/alice-mcp/scripts/start-alice-servers.sh --debug
   ```
3. Verify the Python virtual environment is correctly set up and activated
4. Check if the MCP server path is correctly set in the environment variables or can be found by the start script

### MCP Server Not Found

If you see a warning about the MCP server not being found:

1. Set the `ALICE_MCP_SERVER_PATH` environment variable in the MCP settings:
   ```json
   "env": {
     "ALICE_API_URL": "http://127.0.0.1:8000",
     "ALICE_MCP_SERVER_PATH": "/absolute/path/to/mcp/server/build/index.js"
   }
   ```
2. Ensure the MCP server is built correctly and the JavaScript files exist

### Port Conflicts

If there's a port conflict (another service using port 8000):

1. Modify the port in `scripts/start-alice-servers.sh`
2. Update the `ALICE_API_URL` environment variable accordingly

## Advanced Configuration

### Custom Database Location

By default, Alice uses a SQLite database in the project root. To change this:

1. Create a `.env` file in the alice-mcp directory
2. Add `DATABASE_URL=sqlite:///path/to/your/database.db`

### Custom MCP Server Path

The start script will try to locate the MCP server in several common locations:

1. The path specified in the `ALICE_MCP_SERVER_PATH` environment variable (recommended)
2. Standard Cline MCP locations (`~/Documents/Cline/MCP/alice-mcp-server/build/index.js`)
3. Alternative build directories (`~/Documents/Cline/MCP/alice-mcp-server/dist/index.js`)
4. Relative to the project root

If none of these work, you can explicitly set the path with:
```
export ALICE_MCP_SERVER_PATH="/path/to/your/alice-mcp-server/build/index.js"
```

## Updates and Maintenance

To update Alice:

1.  **Update the Main Alice Project Source Code:**
    This is the primary repository containing the FastAPI backend and the MCP server template.
    ```bash
    cd /path/to/your/main/alice-project # (e.g., where you cloned alice-mcp or your project is located)
    git pull
    source alice-env/bin/activate # Or your equivalent environment activation
    pip install -r requirements.txt
    ```

2.  **Update and Rebuild the MCP Server:**
    The MCP server runs from the `~/Documents/Cline/MCP/alice-mcp-server` directory (or your custom specified path using the `-d` flag with the setup script). This directory's content is generated from the template in the main Alice project. To update it:
    *   **If you used the setup script (`scripts/setup-alice-mcp.sh`):**
        It's generally safest to re-run the setup script. It should handle copying the updated template from your main Alice project and rebuilding. You might consider removing the existing `~/Documents/Cline/MCP/alice-mcp-server` directory first if you want a completely fresh build, or ensure the script can overwrite existing files (it will prompt you).
        ```bash
        # Navigate to your main Alice project directory
        cd /path/to/your/main/alice-project 
        ./scripts/setup-alice-mcp.sh 
        # If you used a custom directory for the MCP server previously, use the -d flag:
        # ./scripts/setup-alice-mcp.sh -d /your/custom/mcp/server/path
        ```
    *   **If you set up manually or prefer a manual update:**
        a.  Copy the updated template from your main Alice project to the MCP server's source directory:
            ```bash
            cp /path/to/your/main/alice-project/templates/alice-mcp-template.ts ~/Documents/Cline/MCP/alice-mcp-server/src/index.ts
            # Or to your custom MCP server path if different
            # cp /path/to/your/main/alice-project/templates/alice-mcp-template.ts /your/custom/mcp/server/path/src/index.ts
            ```
        b.  Navigate to the MCP server directory and rebuild:
            ```bash
            cd ~/Documents/Cline/MCP/alice-mcp-server 
            # Or cd /your/custom/mcp/server/path
            npm install # If dependencies in the template might have changed
            npm run build
            ```

    **Important:** The `~/Documents/Cline/MCP/alice-mcp-server` directory (or your custom path) is primarily a build output location for the MCP server. It should not typically be a separate git repository that you `git pull` into if you are using the template-based setup originating from the main Alice project. The source of truth for the MCP server's code is the `templates/alice-mcp-template.ts` file in your main Alice project.

3.  **Restart Cline** to apply any changes to the MCP server configuration or executable.

## Architecture Overview

The Alice system consists of two main components:

1. **FastAPI Backend**: A Python-based REST API that handles all data operations
   - Manages the SQLite database
   - Provides endpoints for projects, tasks, epics, and messages
   - Runs on port 8000 by default

2. **MCP Server**: A Node.js application that implements the Model Context Protocol
   - Interfaces between AI tools and the FastAPI backend
   - Provides standardized tools that conform to the MCP specification
   - Built with TypeScript and the MCP SDK

There are two ways to run the system:

1. **Direct Mode**: Start the FastAPI server manually, and configure Cline to directly run the MCP server
   ```
   # Terminal 1: Start FastAPI server
   cd /path/to/alice-mcp
   source alice-env/bin/activate
   uvicorn app.main:app --reload

   # Cline configuration calls the MCP server directly
   ```

2. **Wrapper Mode**: Use the `start-alice-servers.sh` script to manage both components
   ```
   # Just run the wrapper script
   /bin/zsh /path/to/alice-mcp/scripts/start-alice-servers.sh

   # Cline configuration calls the wrapper script
   ```

The wrapper script approach is more convenient for development, while the direct mode gives more control and is better for production deployments.

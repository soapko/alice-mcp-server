# Alice MCP Installation Guide for Cline

This guide provides step-by-step instructions for installing and configuring the Alice MCP system for use with Cline or similar AI coding assistants. Alice is a two-component system: a FastAPI backend for task management and a Node.js MCP server for integration with AI tools.

## Prerequisites

- **Python 3.8+** installed on your system
- **Node.js 14+** installed on your system
- **Git** for cloning the repository
- **Cline** desktop app installed

## Installation Methods

There are two methods for installing Alice:

1. **Simplified Installation** (Recommended): Uses Cline's MCP server creation capabilities
2. **Manual Installation**: Manually configuring both components

## Simplified Installation (Recommended)

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

You have two options for setting up the MCP server:

#### Option A: Using the Setup Script (Recommended)

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

When working with Cline on any project:

1. First create a project if you haven't already:
   ```
   Use the alice-mcp-server tool to create a project named "your-project-name" 
   with path "/path/to/your/project".
   ```

2. Get the project ID:
   ```
   Use the alice-mcp-server tool to get a project by name "your-project-name".
   ```

3. Use the project ID for all subsequent tasks, epics, and messages:
   ```
   Use the alice-mcp-server tool to create a task with project_id <your-project-id> 
   and title "Implement feature X".
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

1. Update the FastAPI backend:
   ```bash
   cd path/to/alice-mcp
   git pull
   source alice-env/bin/activate
   pip install -r requirements.txt
   ```

2. Update the MCP server if needed (may require rebuilding the TypeScript code)
   ```bash
   cd ~/Documents/Cline/MCP/alice-mcp-server
   # If you're using a git repository for the MCP server:
   git pull
   npm install
   npm run build
   ```

3. Restart Cline to apply the changes

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

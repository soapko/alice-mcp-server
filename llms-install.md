# Alice MCP Server Installation Guide for Cline

This guide provides step-by-step instructions for installing and configuring the Alice MCP Server for use with Cline.

## Prerequisites

- **Python 3.8+** installed on your system
- **Node.js** installed on your system
- **Git** for cloning the repository
- **Cline** desktop app installed

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-organization/alice-mcp.git
cd alice-mcp
```

## Step 2: Setup the Python Environment

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

## Step 3: Configure the MCP Settings for Cline

1. Open the Cline MCP settings file located at:
   - macOS: `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`
   - Windows: `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

2. Add the Alice MCP server configuration to the `mcpServers` object in the settings file:

```json
{
  "mcpServers": {
    "alice-mcp-server": {
      "command": "/bin/zsh",
      "args": ["/FULL/PATH/TO/alice-mcp/scripts/start-alice-servers.sh"],
      "env": {
        "ALICE_API_URL": "http://127.0.0.1:8000"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Replace `/FULL/PATH/TO/alice-mcp` with the absolute path to where you cloned the Alice MCP repository.

## Step 4: Verify the Installation

1. Restart Cline to load the updated MCP settings.

2. In a new Cline conversation, test the Alice MCP server by creating a project:

```
Use the alice-mcp-server tool to create a project named "test-project".
```

If the installation was successful, Cline should be able to access the Alice MCP tools and create the project.

## Step 5: Using Alice in Your Workflow

When working with Cline on any project:

1. First create a project if you haven't already:
   ```
   Use the alice-mcp-server tool to create a project named "your-project-name".
   ```

2. Get the project ID:
   ```
   Use the alice-mcp-server tool to get a project by name "your-project-name".
   ```

3. Use the project ID for all subsequent tasks, epics, and messages:
   ```
   Use the alice-mcp-server tool to create a task with project_id "your-project-id".
   ```

## Troubleshooting

### Server Not Starting

If the MCP server fails to start:

1. Check the absolute path in your MCP settings file
2. Try running the start script manually:
   ```bash
   /bin/zsh /path/to/alice-mcp/scripts/start-alice-servers.sh --debug
   ```
3. Verify the Python virtual environment is correctly set up and activated

### Port Conflicts

If there's a port conflict (another service using port 8000):

1. Modify the `scripts/start-alice-servers.sh` script to use a different port (e.g., 8001)
2. Update the `ALICE_API_URL` environment variable in the MCP settings accordingly

### Connection Errors

If Cline can't connect to the MCP server:

1. Ensure the FastAPI server is running (should show "FastAPI server is responding" in the terminal)
2. Verify the path to the start script in the MCP settings is correct
3. Check that the environment variables are set correctly

## Advanced Configuration

### Custom Database Location

By default, Alice uses a SQLite database in the project root. To change this:

1. Create a `.env` file in the alice-mcp directory
2. Add `DATABASE_URL=sqlite:///path/to/your/database.db`

### MCP Server Storage Path

The start script automatically tries to find the Alice MCP Node.js component in the following locations (in order):

1. Adjacent to your project: `../alice-mcp-server/build/index.js`
2. In the standard Cline MCP directory: `$HOME/Documents/Cline/MCP/alice-mcp-server/build/index.js`
3. In a local node-mcp subdirectory: `./node-mcp/build/index.js`

You have two options to specify a different location:

1. **Environment Variable (Recommended)**: Set the `NODE_MCP_PATH` environment variable in your MCP settings configuration:
   ```json
   "env": {
     "ALICE_API_URL": "http://127.0.0.1:8000",
     "NODE_MCP_PATH": "/path/to/your/alice-mcp-server/build/index.js"
   }
   ```

2. **Script Modification**: Alternatively, you can modify the location detection logic in the `scripts/start-alice-servers.sh` script if needed.

## Updates and Maintenance

To update the Alice MCP server:

1. Pull the latest changes: `git pull`
2. Update dependencies: `pip install -r requirements.txt`
3. Restart Cline to apply the changes

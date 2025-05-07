#!/bin/bash
# Alice MCP Setup Script
# 
# This script automates the setup of the Alice MCP server, which integrates
# with the Alice FastAPI backend for task management.
#
# It performs the following steps:
# 1. Checks for prerequisites (Node.js, npm)
# 2. Creates the MCP server directory if it doesn't exist
# 3. Sets up the TypeScript project
# 4. Copies the template file
# 5. Installs dependencies
# 6. Builds the TypeScript code
# 7. Updates MCP settings file
# 8. Tests the connection

set -e # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_MCP_DIR="$HOME/Documents/Cline/MCP/alice-mcp-server"
ALICE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TEMPLATE_FILE="$ALICE_ROOT/templates/alice-mcp-template.ts"
CLINE_SETTINGS_DIR="$HOME/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings"
CLINE_SETTINGS_FILE="$CLINE_SETTINGS_DIR/cline_mcp_settings.json"
ALICE_API_URL="http://127.0.0.1:8000"

# Parse command line arguments
MCP_DIR="$DEFAULT_MCP_DIR"
VERBOSE=false

while getopts "d:v" opt; do
  case $opt in
    d) MCP_DIR="$OPTARG" ;;
    v) VERBOSE=true ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
  esac
done

# Display logo and info
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║             ALICE MCP SETUP            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo

# Function for verbose logging
log() {
  if [ "$VERBOSE" = true ]; then
    echo "$1"
  fi
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command -v node &> /dev/null; then
  echo -e "${RED}Error: Node.js is not installed.${NC}"
  echo "Please install Node.js from https://nodejs.org/en/download/"
  exit 1
fi

if ! command -v npm &> /dev/null; then
  echo -e "${RED}Error: npm is not installed.${NC}"
  echo "Please install npm, which usually comes with Node.js"
  exit 1
fi

NODE_VERSION=$(node -v | cut -d 'v' -f 2)
echo -e "Node.js: ${GREEN}v$NODE_VERSION${NC} ✓"

NPM_VERSION=$(npm -v)
echo -e "npm: ${GREEN}v$NPM_VERSION${NC} ✓"

# Ensure template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
  echo -e "${RED}Error: Template file not found: $TEMPLATE_FILE${NC}"
  exit 1
fi

echo -e "Template file: ${GREEN}Found${NC} ✓"
echo

# Create MCP server directory
echo -e "${BLUE}Setting up MCP server directory...${NC}"
if [ -d "$MCP_DIR" ]; then
  echo -e "${YELLOW}Warning: Directory already exists: $MCP_DIR${NC}"
  read -p "Do you want to continue and potentially overwrite existing files? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup aborted."
    exit 1
  fi
else
  echo "Creating directory: $MCP_DIR"
  mkdir -p "$MCP_DIR"
fi

# Create TypeScript project
echo -e "${BLUE}Setting up TypeScript project...${NC}"
cd "$MCP_DIR"

# Initialize package.json if it doesn't exist
if [ ! -f "package.json" ]; then
  echo "Initializing npm project..."
  npm init -y > /dev/null
  
  # Update package.json to add build script
  log "Adding build script to package.json..."
  TMP_FILE=$(mktemp)
  jq '.type = "module" | .scripts.build = "tsc && chmod +x build/index.js"' package.json > "$TMP_FILE"
  mv "$TMP_FILE" package.json
else
  echo -e "${YELLOW}package.json already exists, keeping existing configuration${NC}"
fi

# Create or update tsconfig.json
echo "Creating TypeScript configuration..."
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

# Create src directory
mkdir -p src

# Copy template file
echo -e "${BLUE}Copying template file...${NC}"
cp "$TEMPLATE_FILE" src/index.ts
echo -e "${GREEN}Template copied to src/index.ts${NC} ✓"

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
echo "Installing TypeScript and Node.js type definitions..."
npm install --save-dev typescript @types/node

echo "Installing MCP SDK and Axios..."
npm install @modelcontextprotocol/sdk axios

# Build the TypeScript code
echo -e "${BLUE}Building TypeScript code...${NC}"
npm run build

BUILD_RESULT=$?
if [ $BUILD_RESULT -ne 0 ]; then
  echo -e "${RED}Error: Build failed. Please check for TypeScript errors in src/index.ts${NC}"
  exit 1
fi

echo -e "${GREEN}Build successful!${NC} ✓"
echo

# Update MCP settings file
echo -e "${BLUE}Updating MCP settings...${NC}"

# Check if Cline settings directory exists
if [ ! -d "$CLINE_SETTINGS_DIR" ]; then
  echo -e "${YELLOW}Warning: Cline settings directory not found: $CLINE_SETTINGS_DIR${NC}"
  echo "Skipping MCP settings update. Please manually update your Cline settings."
else
  # Create settings file if it doesn't exist
  if [ ! -f "$CLINE_SETTINGS_FILE" ]; then
    echo "Creating new Cline MCP settings file..."
    mkdir -p "$CLINE_SETTINGS_DIR"
    echo '{"mcpServers":{}}' > "$CLINE_SETTINGS_FILE"
  fi
  
  # Check if file is valid JSON
  if ! jq empty "$CLINE_SETTINGS_FILE" 2>/dev/null; then
    echo -e "${RED}Error: $CLINE_SETTINGS_FILE is not valid JSON${NC}"
    echo "Please fix the file manually and then run this script again."
    exit 1
  fi
  
  # Update settings file
  echo "Updating Cline MCP settings file..."
  TMP_FILE=$(mktemp)
  
  # Read current settings and add/update alice-mcp-server
  jq --arg mcp_path "$MCP_DIR/build/index.js" '.mcpServers["alice-mcp-server"] = {
    "command": "node",
    "args": [$mcp_path],
    "env": {
      "ALICE_API_URL": "'"$ALICE_API_URL"'"
    },
    "disabled": false,
    "autoApprove": []
  }' "$CLINE_SETTINGS_FILE" > "$TMP_FILE"
  
  mv "$TMP_FILE" "$CLINE_SETTINGS_FILE"
  echo -e "${GREEN}MCP settings updated${NC} ✓"
fi

# Final instructions
echo
echo -e "${GREEN}✓ Alice MCP Server setup complete!${NC}"
echo
echo -e "${BLUE}Next steps:${NC}"
echo "1. Start the Alice FastAPI backend:"
echo "   cd $ALICE_ROOT && source alice-env/bin/activate && uvicorn app.main:app --reload"
echo
echo "2. Restart Cline to load the updated MCP settings"
echo
echo "3. Test the connection by creating a project in a new Cline conversation:"
echo "   \"Use the alice-mcp-server tool to create a project named \"test-project\" with"
echo "    path \"/path/to/your/project\".\""
echo
echo -e "${BLUE}For troubleshooting and advanced configuration, see:${NC}"
echo "   $ALICE_ROOT/llms-install.md"
echo

echo -e "${BLUE}MCP Server location:${NC} $MCP_DIR/build/index.js"
echo -e "${BLUE}Cline settings file:${NC} $CLINE_SETTINGS_FILE"
echo

#!/bin/zsh

# Get the directory where the script resides
SCRIPT_DIR=$(dirname "$0")
PROJECT_ROOT=$(cd "$SCRIPT_DIR/.." && pwd) # Assumes script is in project_root/scripts

# Navigate to the FastAPI project directory
cd "$PROJECT_ROOT" || { echo "Failed to cd to $PROJECT_ROOT"; exit 1; }

# Activate the Python virtual environment
echo "Activating Python virtual environment..."
source alice-env/bin/activate

# Ensure all dependencies are installed
echo "Checking for dependencies..."
pip install -r requirements.txt >/dev/null
# Install any missing packages that may not be in requirements.txt
pip install sse-starlette >/dev/null

# Start FastAPI server in the background
echo "Starting FastAPI server (uvicorn app.main:app --reload --port 8000)..."
uvicorn app.main:app --reload --port 8000 &
FASTAPI_PID=$!
echo "FastAPI server started with PID: $FASTAPI_PID"

# Wait for FastAPI server to start up
echo "Waiting for FastAPI server to initialize (5 seconds)..."
sleep 5

# Verify FastAPI server is running
MAX_RETRIES=5
RETRY_INTERVAL=2
retry_count=0
server_ready=false

echo "Verifying FastAPI server availability..."
while [ $retry_count -lt $MAX_RETRIES ]; do
    if curl -s http://127.0.0.1:8000 > /dev/null; then
        echo "✅ FastAPI server is responding at http://127.0.0.1:8000"
        server_ready=true
        break
    else
        retry_count=$((retry_count+1))
        if [ $retry_count -lt $MAX_RETRIES ]; then
            echo "Retry $retry_count/$MAX_RETRIES: FastAPI server not responding yet, waiting ${RETRY_INTERVAL}s..."
            sleep $RETRY_INTERVAL
        fi
    fi
done

if [ "$server_ready" = false ]; then
    echo "❌ WARNING: FastAPI server is not responding after multiple attempts."
    echo "   The MCP server may fail to connect to it."
    echo "   You can try to restart this script or check for errors in another terminal."
    echo "   Continuing to start MCP server anyway..."
else
    echo "FastAPI endpoint verified! Server is running properly."
fi

# Function to clean up background process on exit
cleanup() {
    echo "Stopping FastAPI server (PID: $FASTAPI_PID)..."
    # Check if the process exists before trying to kill
    if ps -p $FASTAPI_PID > /dev/null; then
       kill $FASTAPI_PID
       wait $FASTAPI_PID 2>/dev/null # Wait for it to actually terminate
       echo "FastAPI server stopped."
    else
       echo "FastAPI server (PID: $FASTAPI_PID) already stopped."
    fi
    exit 0
}

# Trap signals to ensure cleanup
trap cleanup SIGINT SIGTERM

# Export API URL as an environment variable for the MCP server to use
export ALICE_API_URL="http://127.0.0.1:8000"
echo "Set environment variable ALICE_API_URL=$ALICE_API_URL"

# Start the Node MCP server in the foreground
# This keeps the script running until the MCP server stops
MCP_SERVER_PATH="/Users/karl/Documents/Cline/MCP/alice-mcp-server/build/index.js"
echo "Starting Alice MCP server (node $MCP_SERVER_PATH)..."

# Check if in debug mode
if [[ "$1" == "--debug" ]]; then
    echo "Running in debug mode..."
    NODE_OPTIONS="--trace-warnings" node "$MCP_SERVER_PATH"
else
    node "$MCP_SERVER_PATH"
fi

# If the node process exits naturally, run cleanup
echo "Alice MCP server process exited."
cleanup

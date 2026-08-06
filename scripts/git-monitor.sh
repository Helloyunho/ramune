#!/bin/bash
# yes gemini made it cuz do i actually have to use
# my brain to make this little script?

INTERVAL=60
BRANCH=$(git branch --show-current 2>/dev/null)

if [ -z "$BRANCH" ]; then
    echo "Error: Not a git repository."
    exit 1
fi

COMMAND="uv run main.py"

run_command() {
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "[Git Watch] Stopping old process ($PID)..."
        kill "$PID"
        wait "$PID" 2>/dev/null
    fi
    echo "[Git Watch] Starting: $COMMAND"
    $COMMAND &
    PID=$!
}

cleanup() {
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "[Git Watch] Stopping process ($PID)..."
        kill "$PID"
        wait "$PID" 2>/dev/null
    fi
}

# catch SIGINT and SIGTERM to clean up the child process
trap 'echo "[Git Watch] Stopping..."; cleanup; exit 0' SIGINT SIGTERM

# Initial start
run_command

# Main watch loop
while true; do
    sleep "$INTERVAL"
    
    # Fetch quiet updates
    git fetch -q
    
    # Check if local branch is behind remote branch
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse "@{u}")
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "[Git Watch] New updates detected. Pulling..."
        git pull -q
        run_command
    fi
done

#!/bin/bash
# Heartbeat orchestrator shell wrapper
# Runs the Python heartbeat script with proper environment

set -e

# Load environment variables
if [ -f "$(dirname "$0")/../../.env" ]; then
    export $(cat "$(dirname "$0")/../../.env" | grep -v "^#" | xargs)
fi

# Required env vars
if [ -z "$PAPERCLIP_API_URL" ] || [ -z "$PAPERCLIP_API_KEY" ]; then
    echo "ERROR: PAPERCLIP_API_URL and PAPERCLIP_API_KEY must be set" >&2
    exit 1
fi

# Run heartbeat script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/heartbeat.py"

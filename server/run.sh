#!/bin/bash
# FormAgent Server Startup Script
# This script starts the FormAgent server component using a virtual environment

# Set terminal colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════╗"
echo "║         FormAgent Server Startup           ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# Default values
HOST="127.0.0.1"
PORT="5000"
DB_PATH="$HOME/.formAgent/formAgent.db"
VENV_DIR=".venv"

# Display help information
show_help() {
    echo -e "${YELLOW}Usage:${NC} ./run.sh [options]"
    echo
    echo "Options:"
    echo "  -h, --help             Show this help message"
    echo "  --host HOST            Set server host address (default: 127.0.0.1)"
    echo "  --port PORT            Set server port (default: 5000)"
    echo "  --db PATH              Set custom database path"
    echo "  --venv-dir DIR         Set virtual environment directory (default: .venv)"
    echo
    echo "Example:"
    echo "  ./run.sh --port 8080"
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --db)
            DB_PATH="$2"
            shift 2
            ;;
        --venv-dir)
            VENV_DIR="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            show_help
            ;;
    esac
done

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not in your PATH${NC}"
    exit 1
fi

# Check if server.py exists
if [ ! -f "server.py" ]; then
    echo -e "${RED}Error: server.py not found. Make sure you're running this from the server directory${NC}"
    exit 1
fi

# Setup virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create virtual environment${NC}"
        echo -e "${YELLOW}Try installing python3-venv package if using Ubuntu/Debian: sudo apt install python3-venv${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Check if requirements are installed
echo -e "${BLUE}Installing Python requirements...${NC}"
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to install Python requirements${NC}"
        deactivate
        exit 1
    fi
fi

# Create data directory if it doesn't exist
DB_DIR=$(dirname "$DB_PATH")
mkdir -p "$DB_DIR"

# Start the server
start_server() {
    echo -e "${GREEN}Starting FormAgent server on $HOST:$PORT...${NC}"
    echo -e "${YELLOW}Database path: $DB_PATH${NC}"
    echo
    
    # Execute the server
    python server.py --host "$HOST" --port "$PORT" --db "$DB_PATH"
    
    # Deactivate virtual environment when done
    deactivate
}

# Main execution
start_server
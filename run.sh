#!/bin/bash
# FormAgent Server Startup Script
# This script starts the FormAgent server component

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

# Display help information
show_help() {
    echo -e "${YELLOW}Usage:${NC} ./run.sh [options]"
    echo
    echo "Options:"
    echo "  -h, --help             Show this help message"
    echo "  --host HOST            Set server host address (default: 127.0.0.1)"
    echo "  --port PORT            Set server port (default: 5000)"
    echo "  --db PATH              Set custom database path"
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
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            show_help
            ;;
    esac
done

# Make the server script executable if it isn't already
chmod +x server/run.sh

# Function to start the server
start_server() {
    echo -e "${GREEN}Starting FormAgent server...${NC}"
    
    # Start the server
    cd server
    ./run.sh --host "$HOST" --port "$PORT" --db "$DB_PATH"
    SERVER_STATUS=$?
    cd ..
    
    return $SERVER_STATUS
}

# Function to handle script termination
cleanup() {
    echo -e "\n${YELLOW}Shutting down FormAgent...${NC}"
    echo -e "${GREEN}FormAgent shut down successfully${NC}"
    exit 0
}

# Set up cleanup for when script is terminated
trap cleanup INT TERM

# Main execution
echo -e "${YELLOW}Starting FormAgent Server${NC}"
echo -e "${BLUE}The browser extension must be loaded manually into your browser${NC}"
echo -e "${BLUE}See the README.md file for instructions${NC}"
echo

start_server
SERVER_STATUS=$?

if [ $SERVER_STATUS -ne 0 ]; then
    echo -e "${RED}Server startup failed${NC}"
    exit 1
fi

exit 0
#!/bin/bash
# start_formagent.sh - Launcher script for FormAgent
# 
# This script provides a convenient way to start the FormAgent application
# with common options and configurations.

# Default options
BROWSER="firefox"
DEBUG_MODE=false
FILL_HIDDEN=false
INTERVAL=2.0

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --chrome)
      BROWSER="chrome"
      shift
      ;;
    --firefox)
      BROWSER="firefox"
      shift
      ;;
    --safari)
      BROWSER="safari"
      shift
      ;;
    --debug)
      DEBUG_MODE=true
      shift
      ;;
    --fill-hidden)
      FILL_HIDDEN=true
      shift
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --help)
      echo "FormAgent - Intelligent Web Form Auto-Filling Agent"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --chrome            Use Chrome browser"
      echo "  --firefox           Use Firefox browser (default)"
      echo "  --safari            Use Safari browser (macOS only)"
      echo "  --debug             Enable debug mode"
      echo "  --fill-hidden       Fill hidden form fields"
      echo "  --interval VALUE    Set scanning interval in seconds (default: 2.0)"
      echo "  --help              Show this help message"
      echo ""
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run '$0 --help' for usage information."
      exit 1
      ;;
  esac
done

# Build command
CMD="python3 ${SCRIPT_DIR}/formagent.py --browser ${BROWSER} --interval ${INTERVAL}"

if [ "$DEBUG_MODE" = true ]; then
  CMD="${CMD} --debug"
fi

if [ "$FILL_HIDDEN" = true ]; then
  CMD="${CMD} --fill-hidden"
fi

# Run the command
echo "Starting FormAgent with ${BROWSER} browser..."
echo "Press Ctrl+C to stop"
echo ""

eval "${CMD}"
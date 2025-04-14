#!/usr/bin/env python3
"""
FormFiller - Web Form Auto-Filler Tool

This script serves as the main entry point for the FormFiller tool suite.
It provides a unified interface to launch different browser auto-fillers.
"""

import argparse
import os
import sys
import subprocess
import logging
from datetime import datetime

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"formfiller_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("formfiller")

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="FormFiller - Web Form Auto-Filler Tool")
    parser.add_argument("--browser", choices=["firefox", "chrome", "safari"], default="firefox",
                        help="Choose which browser to use")
    parser.add_argument("--attach", action="store_true", 
                        help="Attach to an existing browser session")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Scanning interval in seconds")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode")
    parser.add_argument("--fill-hidden", action="store_true",
                        help="Fill hidden form fields")
    
    args = parser.parse_args()
    
    logger.info(f"Starting FormFiller with browser: {args.browser}")
    
    if args.browser == "firefox":
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   "src", "browsers", "firefox_auto_filler.py")
    elif args.browser == "chrome":
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   "src", "browsers", "chrome_auto_filler.py")
    elif args.browser == "safari":
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   "src", "browsers", "safari_auto_filler.py")
    
    cmd = [sys.executable, script_path]
    
    if args.attach:
        cmd.append("--attach")
    
    cmd.extend(["--interval", str(args.interval)])
    
    if args.debug:
        cmd.append("--debug")
        
    if args.fill_hidden:
        cmd.append("--fill-hidden")
    
    logger.info(f"Executing command: {' '.join(cmd)}")
    subprocess.run(cmd)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Process terminated by user")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
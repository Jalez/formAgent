#!/usr/bin/env python3
"""
Chrome browser auto-filler implementation.
This script automates form filling in Chrome browsers using Selenium.
"""

import os
import sys
import argparse
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logger = logging.getLogger("chrome_auto_filler")

def get_chrome_driver(debug=False):
    """Initialize and return a Chrome WebDriver instance."""
    options = Options()
    
    if not debug:
        options.add_argument("--headless")
    
    options.add_argument("--remote-debugging-port=9222")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

def inject_auto_filler_script(driver, fill_hidden=False):
    """Inject the auto-filler JavaScript into the current page."""
    # Get the path to our auto-filler.js script
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(script_dir, "core", "auto-filler.js")
    
    with open(script_path, 'r') as file:
        js_code = file.read()
    
    # Modify configuration if needed
    if fill_hidden:
        js_code = js_code.replace("fillHiddenInputs: false", "fillHiddenInputs: true")
    
    # Inject and execute the script
    driver.execute_script(js_code)
    driver.execute_script("window.autoFiller = initialize();")
    
    logger.info("Auto-filler script injected")

def attach_to_chrome():
    """Attach to an existing Chrome instance with remote debugging enabled."""
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("Successfully attached to Chrome instance")
        return driver
    except Exception as e:
        logger.error(f"Failed to attach to Chrome: {str(e)}")
        logger.error("Make sure Chrome is running with --remote-debugging-port=9222")
        sys.exit(1)

def main():
    """Main function to start the Chrome auto-filler."""
    parser = argparse.ArgumentParser(description="Chrome Form Auto-Filler")
    parser.add_argument("--attach", action="store_true", 
                        help="Attach to an existing Chrome session")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Scanning interval in seconds")
    parser.add_argument("--debug", action="store_true",
                        help="Run in debug mode (non-headless)")
    parser.add_argument("--fill-hidden", action="store_true",
                        help="Fill hidden form fields")
    parser.add_argument("--url", type=str,
                        help="URL to open (if not attaching to existing session)")
    
    args = parser.parse_args()
    
    # Configure logging based on debug flag
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, 
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    logger.info("Starting Chrome auto-filler")
    
    try:
        if args.attach:
            driver = attach_to_chrome()
        else:
            driver = get_chrome_driver(args.debug)
            
            if args.url:
                logger.info(f"Opening URL: {args.url}")
                driver.get(args.url)
            else:
                # Open local test form if no URL specified
                test_form_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                             "test-form.html")
                if os.path.exists(test_form_path):
                    test_form_url = f"file://{test_form_path}"
                    logger.info(f"Opening test form: {test_form_url}")
                    driver.get(test_form_url)
                else:
                    logger.warning("Test form not found. Please provide a URL with --url")
                    driver.get("about:blank")
        
        # Inject auto-filler script
        inject_auto_filler_script(driver, args.fill_hidden)
        
        # Keep the script running
        try:
            while True:
                time.sleep(args.interval)
                # Periodically check if browser is still open
                driver.title  # This will throw an exception if browser is closed
        except Exception as e:
            logger.info("Browser session ended")
    
    except KeyboardInterrupt:
        logger.info("Process terminated by user")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
    finally:
        if 'driver' in locals() and not args.attach:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()
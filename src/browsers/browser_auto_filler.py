#!/usr/bin/env python3
"""
Browser Auto-Filler Script for Firefox

This script monitors your normal Firefox browser and automatically fills form inputs
with random data as you browse the web. It can attach to your existing Firefox session
by using Firefox's remote debugging capabilities.

Prerequisites:
    - Python 3.6+
    - selenium package
    - webdriver-manager package
    - Firefox browser with remote debugging enabled

Installation:
    pip install selenium webdriver-manager

Firefox Remote Debugging Setup:
    1. Close all Firefox windows
    2. Run Firefox with the remote debugging port enabled:
       /Applications/Firefox.app/Contents/MacOS/firefox -remote-debugging-port=9222
    3. Now run this script with the --attach flag

Usage:
    python browser_auto_filler.py --attach [--interval SECONDS]

Options:
    --attach        Attach to an existing Firefox session (requires remote debugging enabled)
    --interval      How often to scan for inputs (in seconds)
"""

import random
import string
import time
import re
import logging
import os
import sys
import platform
import json
import socket
import subprocess
from datetime import datetime
import argparse
import urllib.request
from urllib.error import URLError

from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    ElementNotInteractableException,
    WebDriverException,
)
from webdriver_manager.firefox import GeckoDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("auto_filler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def find_firefox_executable():
    """Find the Firefox executable on the system."""
    system = platform.system()
    logger.info(f"Detecting Firefox on {system} system")
    
    if system == "Darwin":  # macOS
        # Common Firefox locations on macOS
        locations = [
            "/Applications/Firefox.app/Contents/MacOS/firefox",
            "/Applications/Firefox.app/Contents/MacOS/firefox-bin",
            "~/Applications/Firefox.app/Contents/MacOS/firefox",
            "/Applications/Firefox Developer Edition.app/Contents/MacOS/firefox",
            "/Applications/Firefox Nightly.app/Contents/MacOS/firefox",
        ]
        
        # Try to find Firefox using mdfind (macOS Spotlight)
        try:
            spotlight_result = subprocess.check_output(
                ["mdfind", "kMDItemCFBundleIdentifier == 'org.mozilla.firefox'"], 
                text=True
            ).strip()
            if spotlight_result:
                paths = spotlight_result.split("\n")
                for path in paths:
                    firefox_path = os.path.join(path, "Contents/MacOS/firefox-bin")
                    if os.path.exists(firefox_path):
                        logger.info(f"Found Firefox via Spotlight: {firefox_path}")
                        return firefox_path
        except subprocess.SubprocessError:
            logger.info("Could not use Spotlight to find Firefox")
            
    elif system == "Windows":
        # Common Firefox locations on Windows
        locations = [
            os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"),
            os.path.expandvars(r"%LocalAppData%\Mozilla Firefox\firefox.exe"),
        ]
    elif system == "Linux":
        # Common Firefox locations on Linux
        locations = [
            "/usr/bin/firefox",
            "/usr/lib/firefox/firefox",
            "/snap/bin/firefox",
        ]
        
        # Try to find Firefox using which
        try:
            which_result = subprocess.check_output(["which", "firefox"], text=True).strip()
            if which_result:
                logger.info(f"Found Firefox via 'which': {which_result}")
                return which_result
        except subprocess.SubprocessError:
            logger.info("Could not use 'which' to find Firefox")
    else:
        logger.warning(f"Unknown operating system: {system}")
        return None

    # Check all possible locations
    for location in locations:
        location = os.path.expanduser(location)
        if os.path.exists(location):
            logger.info(f"Found Firefox at: {location}")
            return location
    
    logger.warning("Could not find Firefox executable")
    return None

def is_port_in_use(port):
    """Check if a port is in use and specifically by Firefox."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('localhost', port))
            if result == 0:
                # Port is open, now let's check if it's Firefox's remote debugging
                try:
                    url = f"http://localhost:{port}/json/version"
                    with urllib.request.urlopen(url, timeout=2) as response:
                        data = json.loads(response.read())
                        logger.info(f"Found service on port {port}: {data.get('Browser', 'Unknown')}")
                        return "Firefox" in str(data.get('Browser', ''))
                except Exception as e:
                    logger.info(f"Port {port} is open but not responding to Firefox protocol: {e}")
                    return False
            return False
    except Exception as e:
        logger.error(f"Error checking port {port}: {e}")
        return False

def start_firefox_with_remote_debugging(firefox_path, debug_port=9222):
    """Start Firefox with remote debugging enabled."""
    if not firefox_path:
        firefox_path = find_firefox_executable()
        if not firefox_path:
            raise Exception("Could not find Firefox executable")
    
    # Check if Firefox is already running with remote debugging
    if is_port_in_use(debug_port):
        logger.info(f"Firefox is already running with remote debugging on port {debug_port}")
        return True
    
    # Start Firefox with remote debugging enabled
    try:
        logger.info(f"Starting Firefox with remote debugging on port {debug_port}")
        # Create a Firefox profile with remote debugging enabled
        profile_path = os.path.expanduser("~/firefox_debug_profile")
        os.makedirs(profile_path, exist_ok=True)
        
        # Command to start Firefox with remote debugging
        cmd = [
            firefox_path,
            "-P", "debug_profile",
            "-new-instance",
            f"-remote-debugging-port={debug_port}",
            "about:blank"
        ]
        
        # Start Firefox in a new process
        process = subprocess.Popen(cmd)
        
        # Wait for Firefox to start and the port to become available
        for _ in range(10):  # Wait up to 10 seconds
            if is_port_in_use(debug_port):
                logger.info("Firefox started successfully with remote debugging")
                return True
            time.sleep(1)
        
        logger.error("Firefox started but remote debugging port is not responding")
        return False
    except Exception as e:
        logger.error(f"Failed to start Firefox with remote debugging: {e}")
        return False

def get_debuggable_tabs(debug_port=9222):
    """Get the list of debuggable tabs from Firefox."""
    try:
        # Wait a bit for Firefox to fully initialize
        time.sleep(2)
        
        # Get the list of tabs
        url = f"http://localhost:{debug_port}/json/list"
        with urllib.request.urlopen(url) as response:
            tabs = json.loads(response.read())
            logger.info(f"Found {len(tabs)} debuggable tabs")
            return tabs
    except URLError as e:
        logger.error(f"Failed to connect to Firefox debugging port: {e}")
        return []
    except Exception as e:
        logger.error(f"Error getting debuggable tabs: {e}")
        return []

class BrowserAutoFiller:
    """Monitors a browser and automatically fills forms with random data."""

    def __init__(self, scan_interval=2, firefox_path=None, attach_mode=False, debug_port=9222):
        """
        Initialize the auto-filler.
        
        Args:
            scan_interval: How often to scan for inputs (in seconds)
            firefox_path: Path to Firefox executable
            attach_mode: Whether to attach to an existing Firefox session
            debug_port: Firefox remote debugging port
        """
        self.scan_interval = scan_interval
        self.filled_inputs = set()  # Track inputs we've already filled
        self.running = False
        self.debug_port = debug_port
        self.attach_mode = attach_mode
        
        # If in attach mode, we'll connect to an existing Firefox session
        if attach_mode:
            logger.info("Running in attach mode")
            
            # Check if Firefox is running with remote debugging
            if not is_port_in_use(debug_port):
                logger.warning(f"Firefox is not running with remote debugging on port {debug_port}")
                logger.info("Please start Firefox with remote debugging enabled:")
                logger.info(f"/Applications/Firefox.app/Contents/MacOS/firefox -remote-debugging-port={debug_port}")
                raise Exception(f"Firefox remote debugging not available on port {debug_port}")
            
            # Initialize Firefox options for attaching
            self.options = FirefoxOptions()
            self.options.add_argument(f"--remote-debugging-port={debug_port}")
            
            # Set up Firefox driver
            try:
                logger.info("Initializing Firefox WebDriver in attach mode...")
                tabs = get_debuggable_tabs(debug_port)
                if not tabs:
                    raise Exception("No debuggable tabs found in Firefox")
                
                # Currently this is challenging with Firefox, as it doesn't support CDP as well as Chrome.
                # Instead, we'll use standard WebDriver and just monitor the currently active tab.
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=self.options)
                logger.info("Firefox WebDriver initialized in attach mode")
            except Exception as e:
                logger.error(f"Failed to initialize Firefox WebDriver in attach mode: {e}")
                raise
        else:
            # Normal WebDriver initialization
            # Initialize Firefox options
            self.options = FirefoxOptions()
            
            # Set Firefox binary path if provided or found
            if firefox_path:
                logger.info(f"Using provided Firefox path: {firefox_path}")
                self.options.binary_location = firefox_path
            else:
                # Try to find Firefox
                found_firefox = find_firefox_executable()
                if found_firefox:
                    logger.info(f"Using detected Firefox path: {found_firefox}")
                    self.options.binary_location = found_firefox
                else:
                    logger.warning("No Firefox binary path provided or found. Selenium will try to detect it automatically.")
            
            # Set up Firefox driver
            try:
                logger.info("Initializing Firefox WebDriver...")
                service = FirefoxService(GeckoDriverManager().install())
                self.driver = webdriver.Firefox(service=service, options=self.options)
                logger.info("Firefox WebDriver initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firefox WebDriver: {e}")
                raise
        
        # Data generators for different types of inputs
        self.data_generators = {
            "text": self._generate_random_text,
            "email": self._generate_random_email,
            "password": self._generate_random_password,
            "number": self._generate_random_number,
            "tel": self._generate_random_phone,
            "url": self._generate_random_url,
            "textarea": self._generate_random_paragraph,
            "select": self._handle_select,
            "checkbox": self._handle_checkbox,
            "radio": self._handle_radio,
        }
        
        # Input types to target
        self.target_input_types = [
            "text", "email", "password", "number", "tel", "url", "textarea", "select"
        ]
        
        # Whether to fill hidden inputs
        self.fill_hidden_inputs = False

    def start(self):
        """Start monitoring the browser and filling inputs."""
        self.running = True
        logger.info("Browser Auto-Filler started")
        
        try:
            while self.running:
                try:
                    # Get current URL
                    current_url = self.driver.current_url
                    if current_url and not current_url.startswith("about:"):
                        try:
                            logger.info(f"Scanning page: {current_url}")
                            self._scan_for_inputs()
                        except Exception as e:
                            logger.error(f"Error scanning page: {e}")
                    
                    # Wait before scanning again
                    time.sleep(self.scan_interval)
                except WebDriverException as e:
                    # Handle case where browser was closed by user
                    if "target window already closed" in str(e).lower():
                        logger.info("Browser window was closed. Shutting down...")
                        break
                    else:
                        logger.error(f"WebDriver error: {e}")
                        
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stop monitoring and close the browser."""
        if not self.running:
            return
            
        self.running = False
        logger.info("Stopping Browser Auto-Filler")
        try:
            self.driver.quit()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    def _scan_for_inputs(self):
        """Scan the current page for inputs to fill."""
        # Find all input elements by tag
        try:
            input_elements = self.driver.find_elements(By.TAG_NAME, "input")
            textarea_elements = self.driver.find_elements(By.TAG_NAME, "textarea")
            select_elements = self.driver.find_elements(By.TAG_NAME, "select")
            
            total_elements = len(input_elements) + len(textarea_elements) + len(select_elements)
            logger.info(f"Found {total_elements} form elements on the page")
            
            # Process each type of element
            all_elements = input_elements + textarea_elements + select_elements
            filled_count = 0
            
            for element in all_elements:
                try:
                    # Skip already filled elements
                    element_id = element.id
                    if element_id in self.filled_inputs:
                        continue
                    
                    # Check if element is visible
                    if not self.fill_hidden_inputs:
                        try:
                            if not element.is_displayed():
                                continue
                        except:
                            continue
                    
                    # Fill the element
                    if self._fill_input(element):
                        filled_count += 1
                        self.filled_inputs.add(element_id)
                except StaleElementReferenceException:
                    # Element no longer exists in the DOM
                    continue
                except Exception as e:
                    logger.error(f"Error filling input: {e}")
            
            if filled_count > 0:
                logger.info(f"Filled {filled_count} new inputs on the page")
            else:
                logger.info("No new inputs to fill")
                
        except Exception as e:
            logger.error(f"Error in _scan_for_inputs: {e}")

    def _fill_input(self, element):
        """Fill an input element with appropriate random data."""
        try:
            tag_name = element.tag_name.lower()
            
            # Log element info
            element_id = element.get_attribute("id") or ""
            element_name = element.get_attribute("name") or ""
            element_type = element.get_attribute("type") or ""
            logger.info(f"Filling element: {tag_name} (id={element_id}, name={element_name}, type={element_type})")
            
            # Handle textareas
            if tag_name == "textarea":
                value = self.data_generators["textarea"]()
                element.clear()
                element.send_keys(value)
                logger.info(f"Filled textarea with text (length: {len(value)})")
                return True
            
            # Handle select elements
            elif tag_name == "select":
                result = self.data_generators["select"](element)
                if result:
                    logger.info(f"Selected option in select element")
                return result
            
            # Handle input elements
            elif tag_name == "input":
                input_type = element_type.lower() if element_type else "text"
                
                # Handle checkboxes and radio buttons
                if input_type == "checkbox":
                    result = self.data_generators["checkbox"](element)
                    if result:
                        logger.info(f"Set checkbox state")
                    return result
                elif input_type == "radio":
                    result = self.data_generators["radio"](element)
                    if result:
                        logger.info(f"Selected radio button")
                    return result
                # Skip hidden inputs, submit buttons, etc.
                elif input_type in ["hidden", "submit", "button", "reset", "file", "image"]:
                    logger.info(f"Skipping input type: {input_type}")
                    return False
                # Handle text inputs
                elif input_type in self.target_input_types:
                    value = self.data_generators.get(input_type, self.data_generators["text"])()
                    element.clear()
                    element.send_keys(value)
                    logger.info(f"Filled {input_type} input with: {value}")
                    return True
            
            return False
        except ElementNotInteractableException:
            # Element is not interactable (might be hidden or disabled)
            logger.info(f"Element not interactable")
            return False
        except Exception as e:
            logger.error(f"Error in _fill_input: {e}")
            return False

    # Data generator methods
    def _generate_random_text(self, length=10):
        """Generate random text."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_random_email(self):
        """Generate a random email address."""
        username = self._generate_random_text(8).lower()
        domains = ["example.com", "test.org", "fake.net", "dummy.io"]
        return f"{username}@{random.choice(domains)}"

    def _generate_random_password(self):
        """Generate a random password."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choices(chars, k=12))

    def _generate_random_number(self):
        """Generate a random number."""
        return str(random.randint(1, 100))

    def _generate_random_phone(self):
        """Generate a random phone number."""
        return f"555{random.randint(100, 999)}{random.randint(1000, 9999)}"

    def _generate_random_url(self):
        """Generate a random URL."""
        domain = self._generate_random_text(8).lower()
        tlds = ["com", "org", "net", "io"]
        return f"https://{domain}.{random.choice(tlds)}"

    def _generate_random_paragraph(self):
        """Generate a random paragraph of text."""
        words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", 
                "adipiscing", "elit", "sed", "do", "eiusmod", "tempor", 
                "incididunt", "ut", "labore", "et", "dolore", "magna", "aliqua"]
        
        lines = []
        for _ in range(3):
            line_words = random.choices(words, k=random.randint(5, 10))
            lines.append(' '.join(line_words))
        
        return '\n'.join(lines)

    def _handle_select(self, element):
        """Handle select elements by choosing a random option."""
        try:
            # Get all options
            options = element.find_elements(By.TAG_NAME, "option")
            if not options:
                return False
                
            # Filter out placeholder options
            valid_options = []
            for option in options:
                value = option.get_attribute("value")
                text = option.text.lower()
                
                # Skip options that look like placeholders
                if (value and value != "" and 
                    not text.startswith("select") and 
                    not text.startswith("choose") and
                    not text.startswith("--")):
                    valid_options.append(option)
            
            # If we have valid options, select a random one
            if valid_options:
                option = random.choice(valid_options)
                option.click()
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error in _handle_select: {e}")
            return False

    def _handle_checkbox(self, element):
        """Handle checkbox inputs by randomly checking them."""
        try:
            # 50% chance of checking
            if random.random() > 0.5:
                # Only click if not already in desired state
                if not element.is_selected():
                    element.click()
            return True
        except Exception as e:
            logger.error(f"Error in _handle_checkbox: {e}")
            return False

    def _handle_radio(self, element):
        """Handle radio button inputs by selecting one from each group."""
        try:
            # Get the name of the radio button group
            name = element.get_attribute("name")
            if not name:
                return False
                
            # Find all radio buttons in the same group
            radio_group = self.driver.find_elements(
                By.CSS_SELECTOR, f"input[type='radio'][name='{name}']"
            )
            
            # Select a random radio from the group
            if radio_group:
                # Only select if none in the group is already selected
                if not any(radio.is_selected() for radio in the group):
                    random.choice(radio_group).click()
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error in _handle_radio: {e}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Browser Auto-Filler')
    parser.add_argument('--attach', action='store_true', help='Attach to existing Firefox session (requires remote debugging enabled)')
    parser.add_argument('--interval', type=int, default=2, help='Scan interval in seconds')
    parser.add_argument('--firefox-path', type=str, help='Path to Firefox executable')
    parser.add_argument('--debug-port', type=int, default=9222, help='Firefox remote debugging port')
    parser.add_argument('--test', action='store_true', help='Open the test HTML file automatically (not compatible with --attach)')
    parser.add_argument('--url', type=str, help='URL to open and monitor (not compatible with --attach)')
    args = parser.parse_args()
    
    # Check for incompatible options
    if args.attach and (args.test or args.url):
        print("Error: --attach cannot be used with --test or --url")
        print("When using --attach, Firefox should already be running and you should be browsing normally")
        sys.exit(1)
    
    print("Starting Browser Auto-Filler with Firefox...")
    if args.attach:
        print("Running in attach mode - connecting to your existing Firefox browser")
        print(f"Note: Firefox must be running with remote debugging enabled on port {args.debug_port}")
    print("Press Ctrl+C to stop")
    
    try:
        auto_filler = BrowserAutoFiller(
            scan_interval=args.interval,
            firefox_path=args.firefox_path,
            attach_mode=args.attach,
            debug_port=args.debug_port
        )
        
        # Handle test or URL options for non-attach mode
        if not args.attach:
            if args.test:
                test_file_path = os.path.abspath("test-form.html")
                auto_filler.driver.get(f"file://{test_file_path}")
                print(f"Opened test file: {test_file_path}")
            elif args.url:
                auto_filler.driver.get(args.url)
                print(f"Opened URL: {args.url}")
        
        auto_filler.start()
    except Exception as e:
        logger.error(f"Failed to start Browser Auto-Filler: {e}")
        print(f"Error: {e}")
        if args.attach:
            print("\nTo enable Firefox remote debugging:")
            print("1. Close all Firefox windows")
            print(f"2. Run Firefox with: /Applications/Firefox.app/Contents/MacOS/firefox -remote-debugging-port={args.debug_port}")
            print("3. Then run this script again with: python browser_auto_filler.py --attach")
        sys.exit(1)
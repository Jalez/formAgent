#!/usr/bin/env python3
"""
Browser Auto-Filler Script for Safari

This script monitors web pages in Safari and automatically fills form inputs
with random data. It can run in headless mode without showing a browser window.

Prerequisites:
    - Python 3.6+
    - selenium package
    - Safari browser with WebDriver enabled
    - macOS

Installation:
    pip install selenium

Safari WebDriver Setup:
    1. Enable the Develop menu in Safari:
       Safari > Preferences > Advanced > Select "Show Develop menu in menu bar"
    2. Enable Remote Automation:
       Develop > Allow Remote Automation
    3. In Terminal, run:
       safaridriver --enable

Usage:
    python safari_auto_filler.py [--headless] [--test] [--interval SECONDS] [--url URL]

Options:
    --headless     Run in headless mode without showing a browser window
    --test         Open the test HTML file automatically
    --interval     How often to scan for inputs (in seconds)
    --url          URL to open and monitor
"""

import random
import string
import time
import logging
import os
import sys
from datetime import datetime
import argparse
from selenium import webdriver
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    ElementNotInteractableException,
    WebDriverException,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("safari_auto_filler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SafariAutoFiller:
    """Monitors Safari and automatically fills forms with random data."""

    def __init__(self, scan_interval=2, test_mode=False, headless=False):
        """
        Initialize the auto-filler.
        
        Args:
            scan_interval: How often to scan for inputs (in seconds)
            test_mode: If True, open the test HTML file directly
            headless: Whether to run in headless mode
        """
        self.scan_interval = scan_interval
        self.filled_inputs = set()  # Track inputs we've already filled
        self.running = False
        self.test_mode = test_mode
        
        # Initialize Safari options
        self.options = SafariOptions()
        # Safari doesn't support many options, but we can set some basic preferences
        self.options.set_capability("browserName", "safari")
        
        # Note: Safari WebDriver doesn't support true headless mode like Firefox or Chrome
        # We can only mention it in logs for user information
        if headless:
            logger.warning("Safari doesn't support true headless mode. The browser window will still be visible.")
        
        # Set up Safari driver
        try:
            logger.info("Initializing Safari WebDriver...")
            self.driver = webdriver.Safari(options=self.options)
            logger.info("Safari WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Safari WebDriver: {e}")
            logger.error("Make sure you have enabled Safari's WebDriver support:")
            logger.error("1. Enable the Develop menu: Safari > Preferences > Advanced > Select 'Show Develop menu in menu bar'")
            logger.error("2. Enable Remote Automation: Develop > Allow Remote Automation")
            logger.error("3. In Terminal, run: safaridriver --enable")
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
        """Start monitoring Safari and filling inputs."""
        self.running = True
        logger.info("Safari Auto-Filler started")
        
        # If in test mode, open our test HTML file
        if self.test_mode:
            try:
                test_file_path = os.path.abspath("test-form.html")
                logger.info(f"Opening test file: {test_file_path}")
                self.driver.get(f"file://{test_file_path}")
                logger.info(f"Test file opened successfully")
            except Exception as e:
                logger.error(f"Error opening test file: {e}")
                self.stop()
                return
        
        try:
            while self.running:
                try:
                    # Get current URL
                    current_url = self.driver.current_url
                    if current_url and not current_url.startswith("about:") and not current_url.startswith("data:"):
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
        logger.info("Stopping Safari Auto-Filler")
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
    parser = argparse.ArgumentParser(description='Safari Auto-Filler')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (note: Safari does not support true headless mode)')
    parser.add_argument('--interval', type=int, default=2, help='Scan interval in seconds')
    parser.add_argument('--test', action='store_true', help='Open the test HTML file automatically')
    parser.add_argument('--url', type=str, help='URL to open and monitor')
    args = parser.parse_args()
    
    print("Starting Safari Auto-Filler...")
    if args.headless:
        print("Note: Safari doesn't support true headless mode. The browser window will still be visible.")
    print("Press Ctrl+C to stop")
    print("\nIMPORTANT: Before running this script, make sure to enable Safari's WebDriver support:")
    print("1. Enable the Develop menu: Safari > Preferences > Advanced > Select 'Show Develop menu in menu bar'")
    print("2. Enable Remote Automation: Develop > Allow Remote Automation")
    print("3. In Terminal, run: safaridriver --enable")
    
    try:
        auto_filler = SafariAutoFiller(
            scan_interval=args.interval,
            test_mode=args.test,
            headless=args.headless
        )
        
        # If URL is provided, open it
        if args.url and not args.test:
            auto_filler.driver.get(args.url)
            print(f"Opened URL: {args.url}")
            
        auto_filler.start()
    except Exception as e:
        logger.error(f"Failed to start Safari Auto-Filler: {e}")
        print(f"Error: {e}")
        sys.exit(1)
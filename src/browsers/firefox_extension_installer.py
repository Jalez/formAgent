#!/usr/bin/env python3
"""
Browser Auto-Filler Script (Firefox Extension Method)

This script creates a Firefox extension that fills form inputs automatically,
and helps you install it to your existing Firefox browser. This allows the 
auto-filler to work with your normal browsing without restarting Firefox.

Prerequisites:
    - Python 3.6+
    - Firefox browser

Usage:
    python firefox_extension_installer.py [--profile PROFILE_NAME] [--all]

Options:
    --profile   Install to a specific Firefox profile
    --all       Install to all Firefox profiles

Note:
    Due to Firefox's add-on signing requirements, this extension will only
    work with Firefox Developer Edition, Firefox Nightly, or Firefox ESR with
    the 'xpinstall.signatures.required' preference set to false.
    
    For regular Firefox releases, you'll need to:
    1. Install Firefox Developer Edition or Firefox Nightly
    2. Open about:config in the browser
    3. Set xpinstall.signatures.required to false
"""

import os
import sys
import time
import json
import shutil
import random
import string
import logging
import argparse
import subprocess
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("firefox_extension_filler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_firefox_profiles_dir():
    """Get the Firefox profiles directory based on the operating system."""
    home = Path.home()
    
    if sys.platform == "darwin":  # macOS
        return home / "Library/Application Support/Firefox/Profiles"
    elif sys.platform == "win32":  # Windows
        return home / "AppData/Roaming/Mozilla/Firefox/Profiles"
    else:  # Linux and others
        return home / ".mozilla/firefox"

def list_firefox_profiles():
    """List all Firefox profiles found on the system."""
    profiles_dir = get_firefox_profiles_dir()
    
    if not profiles_dir.exists():
        logger.error(f"Firefox profiles directory not found: {profiles_dir}")
        return []
    
    profiles = []
    for item in profiles_dir.iterdir():
        if item.is_dir() and '.' in item.name:  # Firefox profile dirs have a format like "xyz123.default"
            profile_name = item.name.split('.', 1)[1]
            profiles.append((profile_name, item))
    
    return profiles

def create_extension_files(extension_dir):
    """Create the necessary files for the Firefox auto-filler extension."""
    # Create the extension directory if it doesn't exist
    os.makedirs(extension_dir, exist_ok=True)
    
    # Create manifest.json
    manifest = {
        "manifest_version": 2,
        "name": "Form Auto-Filler",
        "version": "1.0",
        "description": "Automatically fills forms with random data",
        "permissions": [
            "activeTab",
            "tabs",
            "<all_urls>"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "content_scripts": [
            {
                "matches": ["<all_urls>"],
                "js": ["content.js"]
            }
        ],
        "browser_action": {
            "default_title": "Form Auto-Filler",
            "default_popup": "popup.html"
        },
        "browser_specific_settings": {
            "gecko": {
                "id": "form-auto-filler@example.com"
            }
        }
    }
    
    with open(os.path.join(extension_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Create background.js
    background_js = """
// Background script for Form Auto-Filler extension
console.log("Form Auto-Filler background script loaded");

// Listen for messages from the content script
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "formFilled") {
    console.log(`Form filled on ${sender.tab.url}: ${message.count} inputs`);
  }
});

// Initialize when installed
browser.runtime.onInstalled.addListener(() => {
  console.log("Form Auto-Filler extension installed");
});

// Send message to content script when toolbar button is clicked
browser.browserAction.onClicked.addListener((tab) => {
  browser.tabs.sendMessage(tab.id, { action: "fillForms" });
});
"""
    
    with open(os.path.join(extension_dir, "background.js"), "w") as f:
        f.write(background_js)
    
    # Create content.js
    content_js = """
// Content script for Form Auto-Filler extension
console.log("Form Auto-Filler content script loaded");

// Configuration
const config = {
  autoFill: true,
  fillHiddenInputs: false,
  targetInputTypes: ['text', 'email', 'password', 'number', 'tel', 'url']
};

// Track filled inputs
const filledInputs = new Set();

// Data generators for different types of inputs
const dataGenerators = {
  text: () => `Random_Text_${Math.floor(Math.random() * 10000)}`,
  email: () => `user${Math.floor(Math.random() * 10000)}@example.com`,
  password: () => `Password${Math.floor(Math.random() * 10000)}!`,
  number: () => Math.floor(Math.random() * 100).toString(),
  tel: () => `555${Math.floor(Math.random() * 10000000).toString().padStart(7, '0')}`,
  url: () => `https://example${Math.floor(Math.random() * 1000)}.com`,
  textarea: () => `This is some random text content.\\nLine ${Math.floor(Math.random() * 100)}`,
  select: (selectElement) => {
    const options = selectElement.querySelectorAll('option');
    if (options.length > 1) {
      // Choose a random non-placeholder option
      const startIndex = options[0].value === '' || options[0].text.includes('Select') ? 1 : 0;
      const randomIndex = startIndex + Math.floor(Math.random() * (options.length - startIndex));
      return options[randomIndex].value;
    }
    return '';
  },
  checkbox: () => Math.random() > 0.5, // 50% chance of checking
  radio: (radioElement) => {
    const name = radioElement.name;
    if (!name) return false;
    
    const radioGroup = document.querySelectorAll(`input[type="radio"][name="${name}"]`);
    if (radioGroup.length === 0) return false;
    
    const randomIndex = Math.floor(Math.random() * radioGroup.length);
    return radioGroup[randomIndex] === radioElement;
  }
};

// Function to fill an input with appropriate random data
function fillInput(input) {
  if (filledInputs.has(input)) return false;
  
  // Check if the input is visible (unless configured to fill hidden inputs)
  if (!config.fillHiddenInputs) {
    const isVisible = input.offsetParent !== null;
    if (!isVisible) return false;
  }

  try {
    let value;
    const tagName = input.tagName.toLowerCase();
    const inputType = input.type ? input.type.toLowerCase() : '';
    
    // Handle different input types
    if (tagName === 'textarea') {
      value = dataGenerators.textarea();
      input.value = value;
    } else if (tagName === 'select') {
      value = dataGenerators.select(input);
      if (value) input.value = value;
    } else if (inputType === 'checkbox') {
      const shouldCheck = dataGenerators.checkbox();
      input.checked = shouldCheck;
    } else if (inputType === 'radio') {
      const shouldCheck = dataGenerators.radio(input);
      if (shouldCheck) input.checked = true;
    } else if (config.targetInputTypes.includes(inputType)) {
      value = dataGenerators[inputType] ? dataGenerators[inputType]() : dataGenerators.text();
      input.value = value;
    } else {
      return false;
    }
    
    // Mark this input as filled
    filledInputs.add(input);
    
    // Dispatch input event to trigger any event listeners
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    
    console.log(`Filled input: ${input.name || input.id || 'unnamed'} with ${value || 'a value'}`);
    return true;
  } catch (error) {
    console.error(`Error filling input:`, error);
    return false;
  }
}

// Function to scan the page for inputs
function scanForInputs() {
  // Get all inputs, textareas, and selects
  const inputElements = document.querySelectorAll('input, textarea, select');
  let filledCount = 0;
  
  inputElements.forEach(input => {
    if (config.autoFill) {
      if (fillInput(input)) {
        filledCount++;
      }
    }
  });
  
  if (filledCount > 0) {
    // Notify the background script
    browser.runtime.sendMessage({ 
      action: "formFilled", 
      count: filledCount 
    });
  }
  
  return filledCount;
}

// Observer to detect new inputs added to the DOM
function setupMutationObserver() {
  const observer = new MutationObserver(mutations => {
    let shouldScan = false;
    
    mutations.forEach(mutation => {
      if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
        shouldScan = true;
      }
    });
    
    if (shouldScan) {
      scanForInputs();
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
  
  return observer;
}

// Run on page load
function initialize() {
  console.log('Auto-filler initialized');
  
  // Initial scan
  const filledCount = scanForInputs();
  
  // Set up mutation observer
  const observer = setupMutationObserver();
  
  // Detect operating system for shortcut keys
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  
  // Add hotkeys
  document.addEventListener('keydown', e => {
    // Mac: Command+Option+F to force fill all inputs
    // Windows/Linux: Ctrl+Alt+F
    if ((isMac && e.metaKey && e.altKey && e.key === 'f') || 
        (!isMac && e.ctrlKey && e.altKey && e.key === 'f')) {
      filledInputs.clear();
      scanForInputs();
      e.preventDefault();
    }
    
    // Mac: Command+Option+S to toggle auto-fill
    // Windows/Linux: Ctrl+Alt+S
    if ((isMac && e.metaKey && e.altKey && e.key === 's') || 
        (!isMac && e.ctrlKey && e.altKey && e.key === 's')) {
      config.autoFill = !config.autoFill;
      console.log(`Auto-fill ${config.autoFill ? 'enabled' : 'disabled'}`);
      e.preventDefault();
    }
  });
  
  return filledCount;
}

// Listen for messages from the background script
browser.runtime.onMessage.addListener((message) => {
  if (message.action === "fillForms") {
    filledInputs.clear();
    const filledCount = scanForInputs();
    console.log(`Filled ${filledCount} inputs`);
  }
});

// Run when the page is loaded
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  initialize();
} else {
  document.addEventListener('DOMContentLoaded', initialize);
}
"""
    
    with open(os.path.join(extension_dir, "content.js"), "w") as f:
        f.write(content_js)
    
    # Create popup.html
    popup_html = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {
      width: 300px;
      padding: 10px;
      font-family: Arial, sans-serif;
    }
    button {
      width: 100%;
      padding: 8px;
      margin-bottom: 10px;
      background-color: #0060df;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    button:hover {
      background-color: #003eaa;
    }
    .status {
      margin-top: 10px;
      padding: 5px;
      background-color: #f0f0f0;
      border-radius: 4px;
    }
    .mac-only, .non-mac {
      display: none;
    }
  </style>
  <script>
    // Detect if we're on a Mac
    document.addEventListener('DOMContentLoaded', function() {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      
      // Show appropriate shortcut instructions
      document.querySelectorAll(isMac ? '.mac-only' : '.non-mac').forEach(el => {
        el.style.display = 'block';
      });
    });
  </script>
</head>
<body>
  <h2>Form Auto-Filler</h2>
  <button id="fillButton">Fill All Forms</button>
  <button id="clearButton">Clear Filled Forms</button>
  <button id="toggleButton">Toggle Auto-Fill</button>
  <div class="status">
    <p>Keyboard shortcuts:</p>
    <ul class="mac-only">
      <li><code>⌘+⌥+F</code> - Force fill all forms</li>
      <li><code>⌘+⌥+S</code> - Toggle auto-fill</li>
    </ul>
    <ul class="non-mac">
      <li><code>Ctrl+Alt+F</code> - Force fill all forms</li>
      <li><code>Ctrl+Alt+S</code> - Toggle auto-fill</li>
    </ul>
  </div>
  <script src="popup.js"></script>
</body>
</html>
"""
    
    with open(os.path.join(extension_dir, "popup.html"), "w") as f:
        f.write(popup_html)
    
    # Create popup.js
    popup_js = """
document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('fillButton').addEventListener('click', () => {
    browser.tabs.query({active: true, currentWindow: true}).then(tabs => {
      browser.tabs.sendMessage(tabs[0].id, {action: "fillForms"});
    });
  });

  document.getElementById('clearButton').addEventListener('click', () => {
    browser.tabs.query({active: true, currentWindow: true}).then(tabs => {
      browser.tabs.sendMessage(tabs[0].id, {action: "clearForms"});
    });
  });

  document.getElementById('toggleButton').addEventListener('click', () => {
    browser.tabs.query({active: true, currentWindow: true}).then(tabs => {
      browser.tabs.sendMessage(tabs[0].id, {action: "toggleAutoFill"});
    });
  });
});
"""
    
    with open(os.path.join(extension_dir, "popup.js"), "w") as f:
        f.write(popup_js)
    
    # Create icons directory
    icons_dir = os.path.join(extension_dir, "icons")
    os.makedirs(icons_dir, exist_ok=True)
    
    # Create simple icon files using base64 encoded PNGs
    fill_48_png = """
iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAABmJLR0QA/wD/AP+gvaeTAAADfUlEQVRoge2ZT0hUQRzHv7+ZXT13TaEOHTznXjpoXjqkJpRmutqfQ5fAiDp0CPJWUNQh6GR/0Og/RAcjqEOniCIijx7UPlO3Z0XpIVMWdd+bOezq7rq7b2ffvhGE74HL/Ga+M9/vZ2bejLwHeHh4eHhUAlJO0PXaRr9O5mNgHAPg20YuAfiRJfPrlFf3JTHuWUcxqyjbgeU7YV+WaRIgwwCqiylPwCiDjdR9fD+fDZUtYMo/0AFSHwPUVnZjADJZQqwrGQ3FK4kvWcC0v6lZ19UkwAflNbfdyxbJjOSS0dDkZlubKWCpP7ijSlMXQDhkU77/JkfgD6+8m58bGM3nFFSw/VLvvtoqZngDwg6H5P8yBOCnNXOzid7hnIPOXw6zAbX9mujVQRKO2s9o+6Ww5JMDcHZg5Fa9ZeZlZbxKplpxnMhUZWqqJbclAFCY4u9jvB0A1hO9w8s6+YZAZEXkyRtDZVTVZ2u2vYTswFjbHJNyGkAzANQTYV8QnAMAxvLElM1xNqD+tjOxs8S0WQCtUdXlRGMkTdimC99JkQKWdK1rnYHWzdKnm81eoymivdZZZZFXQDLapxIQsY8FXMzZ5SlTZ0XXPpeVVeEllIyGppgxCuCJM4JsAoEPpbOxbMNxHICm89Cs2ewNAOciIe8BrCVQTnbKAW5n47pJyLgUhsxGzaWnzGYvAKgAxq2JFxFnBWyxC3u+UbPLUc2uMEYoG0kbNfECQP022e4wVwQo6zI2vLkLQF/BKA8oqYAlbv60AsAXMc6DPYJ2wRUBa1BpGbV3LhvFGBOZ8sXl1+LkDfMwUEIBC72hHiZqFaFvAFMFGNpeMNAjKnxQXNFxDSvPXzyCyA+YDAZejFXEqljw7+sDVOvRVpJ0qyYgDLoxn/kAAHYIJTSSG1MLT2y+kDUm3dyfUzLOKShdA1cYk0T8EUhQCVhh0H5NVXMGVi91HmaCbLDhNnMqzS267zZ2/TQZOJ4j5QmDk84KKG/yCpgLhEcYNAfguYPynpBF07OBIxmAvKKhCcZpAK8ckmdDJeJSz8Mk5BOwxAKPDGIawIzLAtrJImfN+E5CwQIAwLgabRfMtwBMe6QwzeQbNOO8CyUWAACEF5Gc9s/wVhDxBTB9ckGeGfRw50ykN1hqkbK/i/rfie/U2DQqNjU2vYnx8PDw8Kg0vwE8DMoN6YAk4AAAAABJRU5ErkJggg==
"""
    
    fill_96_png = """
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
"""
    
    # Write the PNG icon files
    import base64
    
    with open(os.path.join(icons_dir, "fill-48.png"), "wb") as f:
        f.write(base64.b64decode(fill_48_png))
    
    with open(os.path.join(icons_dir, "fill-96.png"), "wb") as f:
        f.write(base64.b64decode(fill_96_png))
    
    return os.path.join(extension_dir, "manifest.json")

def create_extension_zip(extension_dir, output_file):
    """Create a ZIP file from the extension directory."""
    try:
        import zipfile
        
        # Create a new ZIP file
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through all files in the extension directory
            for root, dirs, files in os.walk(extension_dir):
                for file in files:
                    # Get the full file path
                    file_path = os.path.join(root, file)
                    # Calculate the relative path within the ZIP file
                    # Important: Keep files at the root level, don't include the extension_dir name
                    relative_path = os.path.relpath(file_path, extension_dir)
                    # Add the file to the ZIP with the relative path
                    zipf.write(file_path, relative_path)
        
        logger.info(f"Created extension ZIP file: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Failed to create extension ZIP file: {e}")
        return None

def install_extension_to_profile(profile_path, extension_manifest_path):
    """Install the extension to a Firefox profile."""
    try:
        # Create extensions directory if it doesn't exist
        extensions_dir = os.path.join(profile_path, "extensions")
        os.makedirs(extensions_dir, exist_ok=True)
        
        # Generate a random extension ID
        extension_id = "form-auto-filler@example.com"
        
        # Copy the extension to the profile
        extension_dir = os.path.dirname(extension_manifest_path)
        extension_dest = os.path.join(extensions_dir, extension_id)
        
        # If the destination already exists, remove it
        if os.path.exists(extension_dest):
            if os.path.isdir(extension_dest):
                shutil.rmtree(extension_dest)
            else:
                os.remove(extension_dest)
        
        # Copy the extension
        shutil.copytree(extension_dir, extension_dest)
        
        logger.info(f"Installed extension to profile: {profile_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to install extension to profile: {e}")
        return False

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Install Firefox Form Auto-Filler Extension")
    parser.add_argument("--profile", help="Install to a specific Firefox profile")
    parser.add_argument("--all", action="store_true", help="Install to all Firefox profiles")
    args = parser.parse_args()
    
    # Create a temporary directory for the extension
    with tempfile.TemporaryDirectory() as temp_dir:
        extension_dir = os.path.join(temp_dir, "form-auto-filler")
        
        # Create extension files
        extension_manifest_path = create_extension_files(extension_dir)
        
        if not extension_manifest_path:
            logger.error("Failed to create extension files")
            return 1
        
        # Get Firefox profiles
        profiles = list_firefox_profiles()
        
        if not profiles:
            logger.error("No Firefox profiles found")
            return 1
        
        logger.info(f"Found {len(profiles)} Firefox profiles:")
        for profile_name, profile_path in profiles:
            logger.info(f"  - {profile_name}: {profile_path}")
        
        # Install to specific profile if requested
        if args.profile:
            target_profiles = []
            for profile_name, profile_path in profiles:
                if args.profile.lower() in profile_name.lower():
                    target_profiles.append((profile_name, profile_path))
            
            if not target_profiles:
                logger.error(f"No profile matching '{args.profile}' found")
                return 1
        # Install to all profiles if requested
        elif args.all:
            target_profiles = profiles
        # Otherwise, install to the default profile
        else:
            # Find the default profile (usually has 'default' in the name)
            default_profiles = []
            for profile_name, profile_path in profiles:
                if 'default' in profile_name.lower():
                    default_profiles.append((profile_name, profile_path))
            
            if default_profiles:
                target_profiles = [default_profiles[0]]  # Use the first default profile
            else:
                target_profiles = [profiles[0]]  # Use the first profile if no default found
        
        # Install to target profiles
        for profile_name, profile_path in target_profiles:
            logger.info(f"Installing extension to profile: {profile_name}")
            success = install_extension_to_profile(profile_path, extension_manifest_path)
            
            if success:
                logger.info(f"Successfully installed extension to profile: {profile_name}")
            else:
                logger.error(f"Failed to install extension to profile: {profile_name}")
        
        # Create a ZIP file of the extension for manual installation
        zip_path = os.path.join(os.getcwd(), "form-auto-filler.zip")
        create_extension_zip(extension_dir, zip_path)
        
        logger.info("\n" + "="*50)
        logger.info("Form Auto-Filler Extension Installation Complete!")
        logger.info("="*50)
        logger.info(f"Successfully installed to {len(target_profiles)} profile(s)")
        logger.info(f"A ZIP file of the extension has been created at: {zip_path}")
        logger.info("You can also install it manually from about:debugging in Firefox")
        logger.info("="*50)
        logger.info("To use the extension:")
        logger.info("1. Click the extension icon in the toolbar")
        logger.info("2. Use the buttons to fill forms or clear filled forms")
        logger.info("3. Or use keyboard shortcuts: ")
        logger.info("   - Command+Option+F (Mac) / Ctrl+Alt+F (Windows/Linux) to fill forms")
        logger.info("   - Command+Option+S (Mac) / Ctrl+Alt+S (Windows/Linux) to toggle auto-fill")
        logger.info("="*50)
        
        # Give instructions on how to verify installation
        logger.info("To verify the extension is installed:")
        logger.info("1. Open Firefox")
        logger.info("2. Go to the menu (≡) > Add-ons and themes")
        logger.info("3. Click 'Extensions' on the left side")
        logger.info("4. Check if 'Form Auto-Filler' appears in the list")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())
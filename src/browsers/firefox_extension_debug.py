#!/usr/bin/env python3
"""
Firefox Extension Debugger

This script helps diagnose issues with Firefox extensions, particularly
the Form Auto-Filler extension. It checks if the extension is properly
installed in Firefox profiles and can attempt repairs.

Usage:
    python firefox_extension_debug.py
"""

import os
import sys
import json
import shutil
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("firefox_extension_debug.log"),
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

def get_active_profile():
    """Try to determine the active Firefox profile."""
    try:
        if sys.platform == "darwin":  # macOS
            # On macOS, we can try using ps to find the command line of Firefox
            cmd = ["ps", "-xo", "command"]
            output = subprocess.check_output(cmd, text=True)
            for line in output.splitlines():
                if "firefox" in line.lower() and "-P " in line:
                    # Extract profile name from command line
                    start = line.find("-P ") + 3
                    end = line.find(" ", start)
                    if end == -1:
                        end = len(line)
                    profile = line[start:end]
                    return profile
    except Exception as e:
        logger.error(f"Error determining active profile: {e}")
    
    return None

def check_extension_installation(profile_path):
    """Check if the auto-filler extension is installed in the profile."""
    # The extension ID we used
    extension_id = "form-auto-filler@example.com"
    
    # Path to the extensions directory
    extensions_dir = os.path.join(profile_path, "extensions")
    
    # Check if extensions directory exists
    if not os.path.exists(extensions_dir):
        logger.warning(f"Extensions directory does not exist: {extensions_dir}")
        return False, None
    
    # Check for our extension in the directory
    extension_path = os.path.join(extensions_dir, extension_id)
    
    if os.path.exists(extension_path):
        logger.info(f"Extension found at: {extension_path}")
        
        # Check manifest
        manifest_path = os.path.join(extension_path, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                logger.info(f"Extension manifest version: {manifest.get('version', 'unknown')}")
                return True, extension_path
            except Exception as e:
                logger.error(f"Error reading manifest: {e}")
                return True, extension_path
        else:
            logger.warning(f"Extension directory exists but manifest.json not found")
            return True, extension_path
    
    # Also check if any XPI file exists with our extension ID
    for item in os.listdir(extensions_dir):
        if item.endswith(".xpi") and extension_id in item:
            logger.info(f"Extension found as XPI file: {item}")
            return True, os.path.join(extensions_dir, item)
    
    logger.warning(f"Extension not found in profile")
    return False, None

def find_extension_registry(profile_path):
    """Check the extension registry in the profile."""
    # There are multiple possible locations for extension metadata
    registry_paths = [
        os.path.join(profile_path, "extensions.json"),
        os.path.join(profile_path, "extensions", "extensions.json"),
        os.path.join(profile_path, "extension-settings.json")
    ]
    
    for path in registry_paths:
        if os.path.exists(path):
            logger.info(f"Found extension registry at: {path}")
            try:
                with open(path, 'r') as f:
                    registry = json.load(f)
                
                # Search for our extension
                extension_id = "form-auto-filler@example.com"
                found = False
                
                # The structure varies between Firefox versions
                if isinstance(registry, dict) and "addons" in registry:
                    # Newer format
                    for addon_id, addon_data in registry["addons"].items():
                        if extension_id in addon_id:
                            found = True
                            enabled = addon_data.get("active", False)
                            logger.info(f"Found extension in registry, enabled: {enabled}")
                            return True, enabled
                elif isinstance(registry, list):
                    # Older format
                    for addon in registry:
                        if "id" in addon and extension_id in addon["id"]:
                            found = True
                            enabled = addon.get("active", False) or addon.get("enabled", False)
                            logger.info(f"Found extension in registry, enabled: {enabled}")
                            return True, enabled
                
                if not found:
                    logger.warning("Extension not found in registry")
            except Exception as e:
                logger.error(f"Error reading registry: {e}")
    
    logger.warning("Extension registry not found or extension not in registry")
    return False, False

def check_extension_permissions(profile_path):
    """Check if the extension has necessary permissions."""
    # The permissions.sqlite database contains extension permissions
    # For simplicity, we'll just check if it exists
    permissions_db = os.path.join(profile_path, "permissions.sqlite")
    if os.path.exists(permissions_db):
        logger.info(f"Permissions database exists: {permissions_db}")
        return True
    else:
        logger.warning(f"Permissions database not found: {permissions_db}")
        return False

def check_extension_in_profile(profile_name, profile_path):
    """Perform a complete check of the extension in a profile."""
    print(f"\nChecking profile: {profile_name}")
    print(f"Profile path: {profile_path}")
    
    # Check extension installation
    installed, ext_path = check_extension_installation(profile_path)
    print(f"Extension installed: {installed}")
    if ext_path:
        print(f"Extension path: {ext_path}")
    
    # Check extension registry
    in_registry, enabled = find_extension_registry(profile_path)
    print(f"In extension registry: {in_registry}")
    print(f"Extension enabled: {enabled}")
    
    # Check extension permissions
    perms_exist = check_extension_permissions(profile_path)
    print(f"Permissions database exists: {perms_exist}")
    
    return installed, in_registry, enabled

def repair_extension_installation(profile_path, installer_path):
    """Attempt to repair the extension installation."""
    # First, remove any existing installation
    extension_id = "form-auto-filler@example.com"
    extensions_dir = os.path.join(profile_path, "extensions")
    extension_path = os.path.join(extensions_dir, extension_id)
    
    if os.path.exists(extension_path):
        print(f"Removing existing extension directory: {extension_path}")
        try:
            if os.path.isdir(extension_path):
                shutil.rmtree(extension_path)
            else:
                os.remove(extension_path)
        except Exception as e:
            print(f"Error removing existing extension: {e}")
            return False
    
    # Now run the installer script
    try:
        cmd = [sys.executable, installer_path, "--profile", os.path.basename(profile_path)]
        print(f"Running installer: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"Error running installer: {e}")
        return False

def find_installer_script():
    """Find the Firefox extension installer script."""
    script_path = "firefox_extension_installer.py"
    if os.path.exists(script_path):
        return os.path.abspath(script_path)
    
    # Try looking in the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "firefox_extension_installer.py")
    if os.path.exists(script_path):
        return script_path
    
    return None

def dump_extension_about_config(profile_path):
    """Dump extension-related about:config settings."""
    prefs_file = os.path.join(profile_path, "prefs.js")
    if not os.path.exists(prefs_file):
        print(f"Preferences file not found: {prefs_file}")
        return
    
    print("\nExtension-related about:config settings:")
    try:
        with open(prefs_file, 'r') as f:
            for line in f:
                if "extensions." in line or "xpinstall." in line:
                    print(line.strip())
    except Exception as e:
        print(f"Error reading preferences: {e}")

def check_other_installation_methods(profile_path):
    """Check if user has a temporary or development installation."""
    temp_extensions_file = os.path.join(profile_path, "extensions.ini")
    
    if os.path.exists(temp_extensions_file):
        print("\nChecking for temporary installations in extensions.ini:")
        try:
            with open(temp_extensions_file, 'r') as f:
                print(f.read())
        except Exception as e:
            print(f"Error reading extensions.ini: {e}")

def main():
    print("Firefox Extension Debugger")
    print("==========================")
    
    # First, let's get all Firefox profiles
    profiles = list_firefox_profiles()
    
    if not profiles:
        print("No Firefox profiles found on this system.")
        return
    
    print(f"Found {len(profiles)} Firefox profiles:")
    for i, (name, path) in enumerate(profiles):
        print(f"{i+1}. {name} ({path})")
    
    # Try to determine the active profile
    active_profile = get_active_profile()
    if active_profile:
        print(f"\nCurrent active profile: {active_profile}")
    
    # Check each profile
    all_checks = []
    for name, path in profiles:
        installed, in_registry, enabled = check_extension_in_profile(name, path)
        all_checks.append((name, path, installed, in_registry, enabled))
        
        # Print more detailed information
        dump_extension_about_config(path)
        check_other_installation_methods(path)
    
    # Show a summary
    print("\nSummary of extension status:")
    print("-----------------------------")
    for name, path, installed, in_registry, enabled in all_checks:
        status = "✓ Working" if installed and in_registry and enabled else "✗ Not working"
        print(f"{name}: {status}")
    
    # Find installer script for repairs
    installer_path = find_installer_script()
    if not installer_path:
        print("\nCould not find installer script for repairs.")
        return
    
    # Offer to repair installations
    print("\nWould you like to repair the extension installation?")
    print("1. Repair in all profiles")
    print("2. Repair in a specific profile")
    print("3. Exit without repairs")
    
    try:
        choice = int(input("\nEnter your choice (1-3): "))
        
        if choice == 1:
            for name, path, _, _, _ in all_checks:
                print(f"\nRepairing in profile: {name}")
                if repair_extension_installation(path, installer_path):
                    print(f"Repair complete for profile: {name}")
                else:
                    print(f"Repair failed for profile: {name}")
                    
            print("\nRepair operations completed. Please restart Firefox.")
            print("After restarting, verify that the extension appears:")
            print("1. Open Firefox and go to the menu (≡) > Add-ons and themes")
            print("2. Click 'Extensions' on the left side")
            print("3. Check if 'Form Auto-Filler' appears in the list")
            
        elif choice == 2:
            print("\nSelect a profile to repair:")
            for i, (name, _, _, _, _) in enumerate(all_checks):
                print(f"{i+1}. {name}")
                
            prof_choice = int(input("\nEnter profile number: "))
            if 1 <= prof_choice <= len(all_checks):
                name, path, _, _, _ = all_checks[prof_choice-1]
                print(f"\nRepairing in profile: {name}")
                if repair_extension_installation(path, installer_path):
                    print(f"Repair complete for profile: {name}")
                else:
                    print(f"Repair failed for profile: {name}")
                    
                print("\nRepair operation completed. Please restart Firefox.")
                print("After restarting, verify that the extension appears:")
                print("1. Open Firefox and go to the menu (≡) > Add-ons and themes")
                print("2. Click 'Extensions' on the left side")
                print("3. Check if 'Form Auto-Filler' appears in the list")
            else:
                print("Invalid profile selection.")
                
        else:
            print("Exiting without repairs.")
            
    except ValueError:
        print("Invalid input. Exiting.")

if __name__ == "__main__":
    main()
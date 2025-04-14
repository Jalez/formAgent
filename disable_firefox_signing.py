#!/usr/bin/env python3
"""
Firefox Add-on Signature Requirement Disabler

This script helps you disable the add-on signature requirement in Firefox,
which is necessary for using unsigned extensions like the Form Auto-Filler.

It works by modifying the 'xpinstall.signatures.required' preference in the
Firefox profiles' prefs.js files.

WARNING: This script is for development purposes only. Disabling signature
verification reduces security. Use at your own risk.

Usage:
    python disable_firefox_signing.py [--profile PROFILE_NAME] [--enable]

Options:
    --profile   Modify a specific Firefox profile
    --enable    Re-enable signature verification (default is to disable)
    --list      List all Firefox profiles
"""

import os
import sys
import re
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("disable_firefox_signing.log"),
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

def get_firefox_dev_profiles_dir():
    """Get the Firefox Developer Edition profiles directory."""
    home = Path.home()
    
    if sys.platform == "darwin":  # macOS
        return home / "Library/Application Support/Firefox/Profiles"
    elif sys.platform == "win32":  # Windows
        return home / "AppData/Roaming/Mozilla/Firefox Developer Edition/Profiles"
    else:  # Linux and others
        return home / ".mozilla/firefox-developer-edition"

def get_firefox_nightly_profiles_dir():
    """Get the Firefox Nightly profiles directory."""
    home = Path.home()
    
    if sys.platform == "darwin":  # macOS
        return home / "Library/Application Support/Firefox Nightly/Profiles"
    elif sys.platform == "win32":  # Windows
        return home / "AppData/Roaming/Mozilla/Firefox Nightly/Profiles"
    else:  # Linux and others
        return home / ".mozilla/firefox-nightly"

def list_firefox_profiles():
    """List all Firefox profiles found on the system."""
    profiles = []
    
    # Regular Firefox
    regular_profiles_dir = get_firefox_profiles_dir()
    if regular_profiles_dir.exists():
        for item in regular_profiles_dir.iterdir():
            if item.is_dir() and '.' in item.name:
                profile_name = item.name.split('.', 1)[1]
                profiles.append(("Firefox", profile_name, item))
    
    # Firefox Developer Edition
    dev_profiles_dir = get_firefox_dev_profiles_dir()
    if dev_profiles_dir.exists():
        for item in dev_profiles_dir.iterdir():
            if item.is_dir() and '.' in item.name:
                profile_name = item.name.split('.', 1)[1]
                profiles.append(("Firefox Developer Edition", profile_name, item))
    
    # Firefox Nightly
    nightly_profiles_dir = get_firefox_nightly_profiles_dir()
    if nightly_profiles_dir.exists():
        for item in nightly_profiles_dir.iterdir():
            if item.is_dir() and '.' in item.name:
                profile_name = item.name.split('.', 1)[1]
                profiles.append(("Firefox Nightly", profile_name, item))
    
    return profiles

def modify_signature_requirement(profile_path, enable=False):
    """Modify the signature requirement preference in a Firefox profile."""
    prefs_file = profile_path / "prefs.js"
    user_file = profile_path / "user.js"
    
    if not prefs_file.exists():
        logger.error(f"Preferences file not found: {prefs_file}")
        return False
    
    signature_pref = 'user_pref("xpinstall.signatures.required", false);' if not enable else None
    signature_pref_pattern = re.compile(r'user_pref\("xpinstall.signatures.required", (true|false)\);')
    
    # First, try to modify prefs.js
    modified = False
    content = prefs_file.read_text()
    
    if enable and signature_pref_pattern.search(content):
        # Remove the preference to reset to default (which is true)
        content = re.sub(signature_pref_pattern, '', content)
        prefs_file.write_text(content)
        modified = True
    elif not enable:
        if signature_pref_pattern.search(content):
            # Update the existing preference
            content = re.sub(signature_pref_pattern, signature_pref, content)
            prefs_file.write_text(content)
            modified = True
        else:
            # Add the preference at the end
            with open(prefs_file, 'a') as f:
                f.write(f"\n{signature_pref}\n")
            modified = True
    
    # Also add to user.js to make it persistent
    if not enable:
        with open(user_file, 'a+') as f:
            f.seek(0)
            user_content = f.read()
            if not signature_pref_pattern.search(user_content):
                f.write(f"\n{signature_pref}\n")
                modified = True
    
    return modified

def main():
    parser = argparse.ArgumentParser(description="Firefox Add-on Signature Requirement Disabler")
    parser.add_argument("--profile", help="Modify a specific Firefox profile")
    parser.add_argument("--enable", action="store_true", help="Re-enable signature verification")
    parser.add_argument("--list", action="store_true", help="List all Firefox profiles")
    
    args = parser.parse_args()
    
    profiles = list_firefox_profiles()
    
    if args.list or not profiles:
        if not profiles:
            logger.error("No Firefox profiles found")
            return
        
        print("\nAvailable Firefox profiles:")
        print("----------------------------")
        for i, (browser, profile_name, path) in enumerate(profiles, 1):
            print(f"{i}. {browser}: {profile_name}")
            print(f"   Path: {path}")
        
        if not args.list:
            try:
                selection = int(input("\nEnter profile number to modify (or 0 to exit): "))
                if selection == 0:
                    return
                
                selected_profile = profiles[selection - 1]
                profile_path = selected_profile[2]
            except (ValueError, IndexError):
                logger.error("Invalid selection")
                return
        else:
            return
    elif args.profile:
        profile_path = None
        for browser, profile_name, path in profiles:
            if profile_name == args.profile:
                profile_path = path
                break
        
        if not profile_path:
            logger.error(f"Profile '{args.profile}' not found")
            return
    else:
        # Use the default profile if only one exists
        if len(profiles) == 1:
            profile_path = profiles[0][2]
        else:
            print("\nAvailable Firefox profiles:")
            print("----------------------------")
            for i, (browser, profile_name, path) in enumerate(profiles, 1):
                print(f"{i}. {browser}: {profile_name}")
            
            try:
                selection = int(input("\nEnter profile number to modify (or 0 to exit): "))
                if selection == 0:
                    return
                
                selected_profile = profiles[selection - 1]
                profile_path = selected_profile[2]
            except (ValueError, IndexError):
                logger.error("Invalid selection")
                return
    
    action = "enabling" if args.enable else "disabling"
    logger.info(f"{action.capitalize()} signature requirement for profile: {profile_path}")
    
    success = modify_signature_requirement(profile_path, args.enable)
    
    if success:
        status = "enabled" if args.enable else "disabled"
        logger.info(f"Signature requirement successfully {status}")
        
        # Check if this is a regular Firefox profile and provide appropriate guidance
        if any(browser == "Firefox" for browser, _, path in profiles if path == profile_path):
            if not args.enable:
                logger.warning("\nWARNING: You've disabled add-on signing in a regular Firefox profile.")
                logger.warning("This setting will only work in Firefox Developer Edition, Nightly, or ESR.")
                logger.warning("For regular Firefox, you should install Firefox Developer Edition or Nightly.")
                
                print("\nNext steps:")
                print("1. Download Firefox Developer Edition: https://www.mozilla.org/firefox/developer/")
                print("   or Firefox Nightly: https://www.mozilla.org/firefox/channel/desktop/#nightly")
                print("2. After installation, run this script again to disable signing for that profile")
                print("3. Install your extension in the Developer Edition or Nightly browser")
    else:
        logger.error(f"Failed to {action} signature requirement")

if __name__ == "__main__":
    main()
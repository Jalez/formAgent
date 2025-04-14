#!/usr/bin/env python3
"""
Basic tests for the FormFiller utilities
"""

import os
import sys
import unittest

# Add parent directory to path to import modules for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestFormFiller(unittest.TestCase):
    """Test cases for FormFiller functionality"""
    
    def test_imports(self):
        """Test that the main modules can be imported without errors"""
        try:
            import formfiller
            self.assertTrue(True)
        except ImportError:
            self.fail("Failed to import formfiller")
    
    def test_project_structure(self):
        """Test that the project structure is correct"""
        # Check for critical directories
        self.assertTrue(os.path.isdir("src"), "src directory missing")
        self.assertTrue(os.path.isdir("src/core"), "src/core directory missing")
        self.assertTrue(os.path.isdir("src/browsers"), "src/browsers directory missing")
        
        # Check for critical files
        self.assertTrue(os.path.isfile("formfiller.py"), "formfiller.py missing")
        self.assertTrue(os.path.isfile("src/core/auto-filler.js"), "auto-filler.js missing")

if __name__ == "__main__":
    unittest.main()
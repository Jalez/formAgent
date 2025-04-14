#!/usr/bin/env python3
"""
Basic tests for the FormAgent functionality.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import formagent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import formagent

class TestFormAgent(unittest.TestCase):
    """Test cases for FormAgent functionality."""
    
    @patch('subprocess.run')
    def test_main_defaults(self, mock_run):
        """Test that main function works with default arguments."""
        # Simulate command line arguments
        test_args = ['formagent.py']
        with patch.object(sys, 'argv', test_args):
            formagent.main()
            
            # Verify subprocess was called with correct arguments
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            
            # Check if Firefox is the default browser
            self.assertTrue(any('firefox_auto_filler.py' in arg for arg in args))
            
            # Check interval argument
            self.assertIn('--interval', args)
            interval_index = args.index('--interval')
            self.assertEqual(args[interval_index+1], '2.0')  # Default interval
    
    @patch('subprocess.run')
    def test_chrome_browser(self, mock_run):
        """Test using Chrome browser."""
        test_args = ['formagent.py', '--browser', 'chrome']
        with patch.object(sys, 'argv', test_args):
            formagent.main()
            
            # Verify subprocess was called with correct arguments
            args = mock_run.call_args[0][0]
            
            # Check if Chrome is selected
            self.assertTrue(any('chrome_auto_filler.py' in arg for arg in args))
    
    @patch('subprocess.run')
    def test_debug_mode(self, mock_run):
        """Test debug mode flag."""
        test_args = ['formagent.py', '--debug']
        with patch.object(sys, 'argv', test_args):
            formagent.main()
            
            # Verify debug flag is passed
            args = mock_run.call_args[0][0]
            self.assertIn('--debug', args)
    
    @patch('subprocess.run')
    def test_custom_interval(self, mock_run):
        """Test custom interval setting."""
        test_args = ['formagent.py', '--interval', '1.5']
        with patch.object(sys, 'argv', test_args):
            formagent.main()
            
            # Verify interval is passed correctly
            args = mock_run.call_args[0][0]
            interval_index = args.index('--interval')
            self.assertEqual(args[interval_index+1], '1.5')

if __name__ == '__main__':
    unittest.main()
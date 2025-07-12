"""Tests for utility functions."""

import pytest
import sys
import os
from unittest.mock import patch

# Add the backend src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils import ask


class TestHelperFunctions:
    """Test cases for helper utility functions."""

    @patch("builtins.input")
    def test_ask_function(self, mock_input):
        """Test that ask function prompts for input and returns stripped result."""
        mock_input.return_value = "  test response  "

        result = ask("Test prompt: ")

        assert result == "test response"
        mock_input.assert_called_once_with("Test prompt: ")

    @patch("builtins.input")
    def test_ask_function_empty_input(self, mock_input):
        """Test ask function with empty input."""
        mock_input.return_value = "   "

        result = ask("Enter something: ")

        assert result == ""
        mock_input.assert_called_once_with("Enter something: ")

    @patch("builtins.input")
    def test_ask_function_no_whitespace(self, mock_input):
        """Test ask function with input that has no whitespace."""
        mock_input.return_value = "response"

        result = ask("Prompt: ")

        assert result == "response"
        mock_input.assert_called_once_with("Prompt: ")


if __name__ == "__main__":
    pytest.main([__file__])

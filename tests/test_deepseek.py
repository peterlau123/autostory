"""
Unit tests for DeepSeekApi platform.
"""

import unittest
from unittest.mock import patch, MagicMock
from autostory.platforms.deepseek import DeepSeekApi


class TestDeepSeekApi(unittest.TestCase):
    """Test cases for DeepSeekApi class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = DeepSeekApi()

    def test_initialization_without_api_key(self):
        """Test initialization when API key is not available."""
        # API should not be available when no key is configured
        self.assertFalse(getattr(self.api, 'api_available', False))

    def test_parse_input_string_only(self):
        """Test parsing simple string input."""
        messages = self.api._parse_input_to_messages("Hello world")
        expected = [{"role": "user", "content": "Hello world"}]
        self.assertEqual(messages, expected)

    def test_parse_input_with_system_prompt(self):
        """Test parsing input with separate system prompt."""
        messages = self.api._parse_input_to_messages(
            "Hello world",
            system_prompt="You are a helpful assistant"
        )
        expected = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello world"}
        ]
        self.assertEqual(messages, expected)

    def test_parse_input_messages_list(self):
        """Test parsing when input is already a messages list."""
        input_messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello world"}
        ]
        messages = self.api._parse_input_to_messages(input_messages)
        self.assertEqual(messages, input_messages)

    def test_generate_without_api_configured(self):
        """Test generate method when API is not configured."""
        result = self.api.generate("Test prompt")
        self.assertIn("API not configured", result)
        self.assertIn("Test prompt", result)

    def test_generate_with_messages_list(self):
        """Test generate method with messages list input."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello world"}
        ]
        result = self.api.generate(messages)
        self.assertIn("API not configured", result)
        # Should contain the messages in some form
        self.assertIn("system", result.lower() or "user", result.lower())

    def test_generate_text_backward_compatibility(self):
        """Test backward compatibility of generate_text method."""
        result = self.api.generate_text("Test prompt")
        # Should call generate method internally
        self.assertIn("API not configured", result)

    def test_get_key_method(self):
        """Test get_key method."""
        key = self.api.get_key()
        # Should return the configured key (empty in test)
        self.assertEqual(key, self.api.get_config_value('api_key'))


if __name__ == '__main__':
    unittest.main()

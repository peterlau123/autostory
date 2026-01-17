"""
Unit tests for Volcengine platform.
"""

import unittest
from unittest.mock import patch, MagicMock
from autostory.platforms.volcengine import Volcengine, JimengImageGenerator


class TestVolcengine(unittest.TestCase):
    """Test cases for Volcengine platform classes."""

    def test_volcengine_initialization(self):
        """Test Volcengine platform initialization."""
        # This should work even without the volcengine package
        # since we only initialize JimengImageGenerator when needed
        volcengine = Volcengine()
        self.assertIsInstance(volcengine, Volcengine)
        # Check that the property exists (don't call it)
        self.assertTrue(hasattr(Volcengine, 'jimeng_generator'))
        # Check that it's not yet initialized
        self.assertIsNone(volcengine._jimeng_generator)

    def test_volcengine_generate_text_not_implemented(self):
        """Test that generate_text raises NotImplementedError."""
        volcengine = Volcengine()
        with self.assertRaises(NotImplementedError):
            volcengine.generate_text("Hello world")

    def test_volcengine_generate_image_without_api(self):
        """Test generate_image method when API is not available."""
        volcengine = Volcengine()
        # This should fail because JimengImageGenerator requires volcengine package
        with self.assertRaises(ImportError):
            volcengine.generate_image("A beautiful landscape")

    def test_volcengine_generate_generic_string(self):
        """Test generic generate method with string input."""
        volcengine = Volcengine()
        with self.assertRaises(ImportError):
            volcengine.generate("A beautiful landscape")

    def test_volcengine_generate_generic_invalid_input(self):
        """Test generic generate method with invalid input."""
        volcengine = Volcengine()
        with self.assertRaises(ValueError):
            volcengine.generate(123)  # Invalid input type


class TestJimengImageGenerator(unittest.TestCase):
    """Test cases for JimengImageGenerator class."""

    def test_jimeng_initialization_without_volcengine(self):
        """Test JimengImageGenerator initialization when volcengine package is not available."""
        with self.assertRaises(ImportError):
            JimengImageGenerator()

    def test_fix_dimension(self):
        """Test the fix_dimension static method."""
        # Test normal dimensions
        width, height = JimengImageGenerator.fix_dimension(1024, 1024)
        self.assertEqual((width, height), (1024, 1024))

        # Test too small dimensions
        width, height = JimengImageGenerator.fix_dimension(512, 512)
        self.assertEqual((width, height), (1024, 1024))

        # Test too large dimensions
        width, height = JimengImageGenerator.fix_dimension(5000, 5000)
        self.assertEqual((width, height), (4096, 4096))


if __name__ == '__main__':
    unittest.main()

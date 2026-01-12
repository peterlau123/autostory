#!/usr/bin/env python3
"""
Volcengine Platform Module

This module provides Volcengine platform integration with support for both
text generation and image generation services.

Example usage:
    from autostory.platforms.volcengine import Volcengine

    volcengine = Volcengine()
    text_result = volcengine.generate_text("Hello, how are you?")
    image_result = volcengine.generate_image("A beautiful landscape", width=1024, height=1024)
"""

from typing import Optional, Dict, Any
from ...platforms.platform import Platform
from .jimeng import JimengImageGenerator


class Volcengine(Platform):
    """
    Volcengine Platform Class

    Main platform class that provides access to various Volcengine services
    including text generation and image generation.
    """

    def __init__(self, access_key_id: Optional[str] = None, secret_key: Optional[str] = None, **kwargs):
        """
        Initialize Volcengine platform instance.

        Args:
            access_key_id: Volcengine access key ID. If None, uses access configuration.
            secret_key: Volcengine secret key. If None, uses access configuration.
            **kwargs: Additional initialization parameters
        """
        super().__init__('volcengine', **kwargs)

        # Store initialization parameters for lazy initialization
        self._access_key_id = access_key_id
        self._secret_key = secret_key
        self._init_kwargs = kwargs
        self._jimeng_generator = None

    @property
    def jimeng_generator(self):
        """
        Lazy initialization of JimengImageGenerator.

        Returns:
            JimengImageGenerator: The image generator instance

        Raises:
            ImportError: If volcengine package is not available
        """
        if self._jimeng_generator is None:
            self._jimeng_generator = JimengImageGenerator(
                access_key_id=self._access_key_id,
                secret_key=self._secret_key,
                **self._init_kwargs
            )
        return self._jimeng_generator

    def _init_platform(self, **kwargs):
        """
        Platform-specific initialization for Volcengine.

        Args:
            **kwargs: Platform-specific parameters
        """
        # Volcengine platform initialization
        pass

    def generate(self, input_data: Any, **kwargs) -> Any:
        """
        Generate output from input data (generic method).

        Args:
            input_data: Input data for generation
            **kwargs: Generation parameters

        Returns:
            Generated output
        """
        # Default to image generation for string inputs
        if isinstance(input_data, str):
            return self.generate_image(input_data, **kwargs)
        else:
            raise ValueError("Unsupported input data type for generic generate method")

    def generate_text(self, text: str, **kwargs) -> str:
        """
        Generate text from input text.

        Args:
            text: Input text for generation
            **kwargs: Generation parameters

        Returns:
            Generated text

        Raises:
            NotImplementedError: Volcengine platform doesn't support text generation yet
        """
        # Volcengine doesn't have a text generation service in this implementation
        # This could be extended to support other Volcengine services in the future
        raise NotImplementedError("Volcengine platform does not currently support text generation")

    def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate images from text prompt using Jimeng.

        Args:
            prompt: Text prompt for image generation
            **kwargs: Generation parameters (width, height, etc.)

        Returns:
            dict: Result containing 'image_urls' and 'task_id'
        """
        return self.jimeng_generator.generate(prompt, **kwargs)


# Backward compatibility: keep the old class name available
VolcengineImageGenerator = JimengImageGenerator

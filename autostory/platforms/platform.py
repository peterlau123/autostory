"""
Base platform class for all API integrations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from . import get_access_config


class Platform(ABC):
    """
    Abstract base class for all platform integrations.

    Provides common initialization and configuration handling.
    """

    def __init__(self, platform_name: str, **kwargs):
        """
        Initialize the platform with configuration.

        Args:
            platform_name: Name of the platform (used for config lookup)
            **kwargs: Additional initialization parameters
        """
        self.platform_name = platform_name
        self.config = get_access_config(platform_name)
        self._init_platform(**kwargs)

    @abstractmethod
    def _init_platform(self, **kwargs):
        """
        Platform-specific initialization.

        Args:
            **kwargs: Platform-specific parameters
        """
        pass

    @abstractmethod
    def generate(self, input_data: Any, **kwargs) -> Any:
        """
        Generate output from input data.

        Args:
            input_data: Input data for generation
            **kwargs: Generation parameters

        Returns:
            Generated output (type depends on platform)
        """
        pass

    def generate_text(self, text: str, **kwargs) -> str:
        """
        Generate text from input text.

        Args:
            text: Input text for generation
            **kwargs: Generation parameters

        Returns:
            Generated text

        Raises:
            NotImplementedError: If the platform doesn't support text generation
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support text generation")

    def generate_image(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate images from text prompt.

        Args:
            prompt: Text prompt for image generation
            **kwargs: Generation parameters

        Returns:
            dict: Result containing image data

        Raises:
            NotImplementedError: If the platform doesn't support image generation
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support image generation")

    def get_config_value(self, key: str) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key

        Returns:
            Configuration value
        """
        return self.config.get(key)

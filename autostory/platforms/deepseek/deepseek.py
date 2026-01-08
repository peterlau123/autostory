import os
from .. import get_access_config


class DeepSeekApi:
    """
    DeepSeek API integration class.
    """

    def __init__(self):
        """
        Initialize DeepSeek API with access configuration.
        """
        config = get_access_config('deepseek')
        self.api_key = config['api_key']

    def get_key(self) -> str:
        """
        Get the API key for DeepSeek.

        Returns:
            str: The API key
        """
        return self.api_key

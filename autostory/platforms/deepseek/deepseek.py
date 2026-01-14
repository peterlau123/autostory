import os
from typing import Optional, Union, List, Dict, Any
from openai import OpenAI

from ...platforms.platform import Platform


class DeepSeekApi(Platform):
    """
    DeepSeek API integration class using OpenAI SDK.
    """

    def __init__(self, **kwargs):
        """
        Initialize DeepSeek API with access configuration.

        Args:
            **kwargs: Additional initialization parameters
        """
        super().__init__('deepseek', **kwargs)

    def _init_platform(self, **kwargs):
        """
        Platform-specific initialization for DeepSeek.

        Args:
            **kwargs: Platform-specific parameters
        """
        api_key = self.get_config_value('api_key')
        if api_key:
            try:
                # Initialize OpenAI client with DeepSeek endpoint
                self.client = OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                self.api_available = True
            except Exception:
                self.api_available = False
        else:
            self.api_available = False

    def _parse_input_to_messages(self, input_data: Union[str, List[Dict[str, Any]]], **kwargs) -> List[Dict[str, Any]]:
        """
        Parse input data into OpenAI chat messages format.

        Supports multiple input formats:
        1. List of message dictionaries (passed directly)
        2. String with system/user separation
        3. Simple string (treated as user message)

        Args:
            input_data: Input data to parse
            **kwargs: Additional parameters including system_prompt

        Returns:
            list: List of message dictionaries for OpenAI API
        """
        # If input_data is already a list of messages, use it directly
        if isinstance(input_data, list) and input_data:
            return input_data

        messages = []
        system_prompt = kwargs.get('system_prompt')

        # If system jimeng_play_writer is provided separately, use it
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": input_data})
        else:
            # Try to parse combined format, or treat as simple user message
            messages.append({"role": "user", "content": input_data})

        return messages

    def generate(self, input_data: Union[str, List[Dict[str, Any]]], **kwargs) -> str:
        """
        Generate text using DeepSeek API.

        Args:
            input_data: Input jimeng_play_writer/text
            **kwargs: Additional parameters (model, temperature, etc.)

        Returns:
            str: Generated text
        """
        # Check if API is available, otherwise fall back to placeholder
        if not hasattr(self, 'api_available') or not self.api_available:
            return f"DeepSeek response to: {input_data} (API not configured)"

        # Extract parameters with defaults
        model = kwargs.get('model', 'deepseek-chat')# TODO: deepseek-chat or deepseek-reasoner
        temperature = kwargs.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens', 2000)
        stream = kwargs.get('stream', False)

        # Parse input into messages
        messages = self._parse_input_to_messages(input_data, **kwargs)

        try:
            # Make API call
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )

            # Extract response content
            if stream:
                # Handle streaming response
                content = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                return content
            else:
                return response.choices[0].message.content

        except Exception as e:
            # Fall back to placeholder on API errors
            return f"DeepSeek response to: {input_data} (API error: {str(e)})"

    def get_key(self) -> str:
        """
        Get the API key for DeepSeek.

        Returns:
            str: The API key
        """
        return self.get_config_value('api_key')

    # Backward compatibility method
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using DeepSeek API (backward compatibility).

        Args:
            prompt: Input jimeng_play_writer
            **kwargs: Additional parameters

        Returns:
            str: Generated text
        """
        return self.generate(prompt, **kwargs)

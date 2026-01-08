"""
Platform utilities for accessing API keys and configuration.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional


def get_access_config(platform_name: str) -> Dict[str, Any]:
    """
    Get access configuration for a platform using the following priority:
    1. Environment variables
    2. .access.json file in project root
    3. Error with helpful message

    Args:
        platform_name: Name of the platform (e.g., 'volcengine', 'deepseek')

    Returns:
        dict: Configuration dictionary for the platform

    Raises:
        SystemExit: If configuration cannot be found
    """
    # Define platform-specific environment variable mappings
    platform_configs = {
        'volcengine': {
            'env_vars': {
                'access_key_id': 'VOLCENGINE_ACCESS_KEY_ID',
                'secret_key': 'VOLCENGINE_SECRET_KEY'
            },
            'required_keys': ['access_key_id', 'secret_key']
        },
        'deepseek': {
            'env_vars': {
                'api_key': 'DEEP_SEEK_API_KEY'
            },
            'required_keys': ['api_key']
        },
        'azure': {
            'env_vars': {
                'speech_key': 'SPEECH_KEY',
                'endpoint': 'ENDPOINT'
            },
            'required_keys': ['speech_key', 'endpoint']
        },
        'qwen': {
            'env_vars': {
                'api_key': 'QWEN_API_KEY'
            },
            'required_keys': ['api_key']
        }
    }

    if platform_name not in platform_configs:
        print(f"Error: Unknown platform '{platform_name}'", file=sys.stderr)
        sys.exit(1)

    config = platform_configs[platform_name]
    env_vars = config['env_vars']
    required_keys = config['required_keys']

    # First, try to get from environment variables
    result = {}
    missing_from_env = []

    for key_name, env_var in env_vars.items():
        value = os.environ.get(env_var)
        if value:
            result[key_name] = value
        else:
            missing_from_env.append(env_var)

    # If all keys found in environment, return them
    if len(result) == len(required_keys):
        return result

    # If not all keys found in environment, try .access.json file
    project_root = _find_project_root()
    access_file = project_root / '.access.json'

    if access_file.exists():
        try:
            with open(access_file, 'r', encoding='utf-8') as f:
                access_data = json.load(f)

            platform_data = access_data.get('platforms', {}).get(platform_name, {})

            # Fill in missing keys from the access file
            for key_name in required_keys:
                if key_name not in result and key_name in platform_data:
                    result[key_name] = platform_data[key_name]

            # Check if we now have all required keys
            if len(result) == len(required_keys):
                return result

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read .access.json file: {e}", file=sys.stderr)

    # If we still don't have all keys, show error and exit
    missing_keys = [key for key in required_keys if key not in result]

    print(f"Error: Missing required access configuration for platform '{platform_name}'", file=sys.stderr)
    print("Please provide the following:", file=sys.stderr)

    if missing_from_env:
        print("\nOption 1: Set environment variables:", file=sys.stderr)
        for env_var in missing_from_env:
            print(f"  export {env_var}=your_{env_var.lower()}", file=sys.stderr)

    print("\nOption 2: Create .access.json file in project root with content like:", file=sys.stderr)
    template_config = {key: "" for key in required_keys}
    print(f"""  {{
    "platforms": {{
      "{platform_name}": {json.dumps(template_config, indent=6)}
    }}
  }}""", file=sys.stderr)

    print(f"\nSee access-template.json for the full template.", file=sys.stderr)
    sys.exit(1)


def _find_project_root() -> Path:
    """
    Find the project root directory by looking for common project markers.

    Returns:
        Path: Project root directory
    """
    current = Path(__file__).resolve().parent

    # Go up until we find a marker of project root
    for parent in [current] + list(current.parents):
        if (parent / 'pyproject.toml').exists() or \
           (parent / 'setup.py').exists() or \
           (parent / 'requirements.txt').exists() or \
           (parent / '.git').exists():
            return parent

    # Fallback to the autostory directory
    return current.parent

#!/usr/bin/env python3
"""
Autostory Image Generation Driver

This script provides a unified interface for image generation across different platforms.
It automatically discovers available image generation platforms and allows users to select which one to use.

Example usage:
    python -m autostory.image_generate --platform volcengine --jimeng_play_writer "A beautiful landscape"
    python -m autostory.image_generate --list-platforms
"""

import os
import sys
import importlib
import argparse
from typing import Dict, List, Type, Any
import inspect


def discover_image_generators() -> tuple[Dict[str, Type[Any]], Dict[str, str]]:
    """
    Discover all available image generator classes in the platforms directory.

    Returns:
        tuple: (available_generators, unavailable_platforms_with_errors)
    """
    generators = {}
    unavailable = {}

    # Get the platforms directory path
    platforms_dir = os.path.join(os.path.dirname(__file__), 'platforms')

    if not os.path.exists(platforms_dir):
        return generators, unavailable

    # Iterate through platform directories/files
    for item in os.listdir(platforms_dir):
        if item.startswith('_') or item.startswith('.'):
            continue

        platform_path = os.path.join(platforms_dir, item)

        if os.path.isdir(platform_path):
            # Platform is in a subdirectory (like volcengine/)
            platform_name = item
            platform_file = os.path.join(platform_path, f'{item}.py')
            if os.path.exists(platform_file):
                try:
                    # Import the platform module
                    module_name = f'autostory.platforms.{platform_name}.{platform_name}'
                    module = importlib.import_module(module_name)

                    # Find classes ending with "ImageGenerator"
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and
                            name.endswith('ImageGenerator') and
                            hasattr(obj, 'generate')):
                            generators[platform_name] = obj
                            break

                except Exception as e:
                    unavailable[platform_name] = str(e)

        elif os.path.isfile(platform_path) and item.endswith('.py'):
            # Platform is a direct file
            platform_name = item[:-3]  # Remove .py extension
            try:
                module_name = f'autostory.platforms.{platform_name}'
                module = importlib.import_module(module_name)

                # Find classes ending with "ImageGenerator"
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and
                        name.endswith('ImageGenerator') and
                        hasattr(obj, 'generate')):
                        generators[platform_name] = obj
                        break

            except Exception as e:
                unavailable[platform_name] = str(e)

    return generators, unavailable


def get_platform_requirements(platform_class: Type[Any]) -> Dict[str, Any]:
    """
    Get the initialization requirements for a platform class.

    Args:
        platform_class: The image generator class

    Returns:
        dict: Requirements information
    """
    init_signature = inspect.signature(platform_class.__init__)
    params = init_signature.parameters

    # Remove 'self' parameter
    required_params = [p for p in params.values() if p.name != 'self' and p.default == inspect.Parameter.empty]

    return {
        'required_params': [p.name for p in required_params],
        'all_params': list(params.keys())[1:],  # Exclude 'self'
        'docstring': platform_class.__doc__ or "No description available"
    }


def create_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate images using various AI platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --platform volcengine --jimeng_play_writer "A beautiful landscape" --access-key YOUR_KEY --secret-key YOUR_SECRET
  %(prog)s --list-platforms
  %(prog)s --platform-info volcengine

Environment Variables:
  VOLCENGINE_ACCESS_KEY_ID    - Volcengine access key ID
  VOLCENGINE_SECRET_KEY       - Volcengine secret key
        """
    )

    parser.add_argument(
        '--platform', '-p',
        type=str,
        help='Platform to use for image generation'
    )

    parser.add_argument(
        '--list-platforms', '-l',
        action='store_true',
        help='List all available platforms'
    )

    parser.add_argument(
        '--platform-info',
        type=str,
        help='Show detailed information about a specific platform'
    )

    parser.add_argument(
        '--jimeng_play_writer',
        type=str,
        help='Text jimeng_play_writer for image generation'
    )

    parser.add_argument(
        '--ref-image', '-r',
        action='append',
        help='Reference image URLs or local file paths (can be specified multiple times)'
    )

    parser.add_argument(
        '--width', '-w',
        type=int,
        default=1024,
        help='Image width (default: 1024)'
    )

    parser.add_argument(
        '--height',
        type=int,
        default=1024,
        help='Image height (default: 1024)'
    )

    parser.add_argument(
        '--force-single', '-s',
        action='store_true',
        help='Force single image generation'
    )

    parser.add_argument(
        '--access-key', '-k',
        type=str,
        help='Access key ID (platform-specific)'
    )

    parser.add_argument(
        '--secret-key',
        type=str,
        help='Secret key (platform-specific)'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        default=15,
        help='Maximum polling attempts (default: 15)'
    )

    parser.add_argument(
        '--polling-interval',
        type=int,
        default=4,
        help='Seconds between polling attempts (default: 4)'
    )

    return parser


def main():
    """Main function."""
    parser = create_parser()
    args = parser.parse_args()

    # Discover available platforms
    generators, unavailable = discover_image_generators()

    # Handle list platforms
    if args.list_platforms:
        print("Available image generation platforms:")
        if generators:
            for platform_name, generator_class in generators.items():
                requirements = get_platform_requirements(generator_class)
                print(f"  ✓ {platform_name}: {requirements['docstring'].strip().split('.')[0]}")
        else:
            print("  (No platforms currently available)")

        if unavailable:
            print("\nPlatforms with missing dependencies:")
            for platform_name, error in unavailable.items():
                print(f"  ✗ {platform_name}: {error}")

        return

    # Handle platform info
    if args.platform_info:
        platform_name = args.platform_info
        if platform_name in generators:
            generator_class = generators[platform_name]
            requirements = get_platform_requirements(generator_class)
            status = "Available"
            print(f"Platform: {platform_name}")
            print(f"Status: {status}")
            print(f"Description: {requirements['docstring']}")
            print(f"Required parameters: {', '.join(requirements['required_params'])}")
            print(f"All parameters: {', '.join(requirements['all_params'])}")
        elif platform_name in unavailable:
            print(f"Platform: {platform_name}")
            print(f"Status: Unavailable - {unavailable[platform_name]}")
            print("Install missing dependencies to make this platform available.")
        else:
            print(f"Error: Platform '{platform_name}' not found!", file=sys.stderr)
            all_platforms = set(generators.keys()) | set(unavailable.keys())
            print(f"Available platforms: {', '.join(sorted(all_platforms))}", file=sys.stderr)
            sys.exit(1)
        return

    if not generators:
        print("Error: No image generation platforms available!", file=sys.stderr)
        if unavailable:
            print("Platforms found but unavailable due to missing dependencies:", file=sys.stderr)
            for platform_name, error in unavailable.items():
                print(f"  - {platform_name}: {error}", file=sys.stderr)
        sys.exit(1)

    # Check if platform is specified
    if not args.platform:
        print("Error: Please specify a platform with --platform", file=sys.stderr)
        print(f"Available platforms: {', '.join(generators.keys())}", file=sys.stderr)
        print("Use --list-platforms to see all options", file=sys.stderr)
        sys.exit(1)

    if args.platform not in generators:
        print(f"Error: Platform '{args.platform}' not found!", file=sys.stderr)
        print(f"Available platforms: {', '.join(generators.keys())}", file=sys.stderr)
        sys.exit(1)

    # Get the generator class
    generator_class = generators[args.platform]
    requirements = get_platform_requirements(generator_class)

    # Check required parameters
    missing_params = []
    init_kwargs = {}

    for param_name in requirements['required_params']:
        if param_name == 'access_key_id' or param_name == 'access_key':
            value = args.access_key or os.environ.get('VOLCENGINE_ACCESS_KEY_ID')
            if not value:
                missing_params.append('access_key')
            else:
                init_kwargs[param_name] = value
        elif param_name == 'secret_key' or param_name == 'secret':
            value = args.secret_key or os.environ.get('VOLCENGINE_SECRET_KEY')
            if not value:
                missing_params.append('secret_key')
            else:
                init_kwargs[param_name] = value
        else:
            missing_params.append(param_name)

    if missing_params:
        print(f"Error: Missing required parameters for {args.platform}: {', '.join(missing_params)}", file=sys.stderr)
        print("Provide them via command line options or environment variables", file=sys.stderr)
        sys.exit(1)

    # Check if jimeng_play_writer is provided
    if not args.prompt:
        print("Error: Please provide a jimeng_play_writer with --jimeng_play_writer", file=sys.stderr)
        sys.exit(1)

    try:
        # Initialize the generator
        print(f"Initializing {args.platform} image generator...")
        generator = generator_class(**init_kwargs)

        # Process reference images if provided
        processed_ref_images = args.ref_image or []

        # Generate the image
        print(f"Generating image with jimeng_play_writer: '{args.prompt}'")
        if processed_ref_images:
            print(f"Using {len(processed_ref_images)} reference image(s)")

        result = generator.generate(
            prompt=args.prompt,
            width=args.width,
            height=args.height,
            force_single=args.force_single,
            image_urls=processed_ref_images if processed_ref_images else None,
            max_retries=args.max_retries,
            polling_interval=args.polling_interval
        )

        # Display results
        print("\n✓ Generation completed successfully!")
        print(f"Task ID: {result['task_id']}")
        print(f"Generated {len(result['image_urls'])} image(s):")

        for i, url in enumerate(result['image_urls'], 1):
            print(f"  {i}. {url}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

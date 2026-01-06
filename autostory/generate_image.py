#!/usr/bin/env python3
"""
Volcengine Image Generation CLI Tool

This script provides a command-line interface for generating images using Volcengine Jimeng API.
It supports both URL and local file reference images.

Example usage:
    python -m autostory.generate_image --prompt "A beautiful landscape" --ref-image image.jpg
    python -m autostory.generate_image --prompt "A sunset" --ref-image https://example.com/image.jpg --width 2048 --height 1024
    python -m autostory.generate_image --prompt "Test" --access-key YOUR_KEY --secret-key YOUR_SECRET
"""

import os
import sys
import base64
import argparse
from typing import List
from pathlib import Path

from .platforms.volcengine import VolcengineImageGenerator


def upload_local_image(visual_service, local_path: str) -> str:
    """
    Upload a local image file and return the URL.

    For now, converts local images to base64 data URLs.
    If the API requires actual HTTP URLs, you'll need to implement proper upload to Volcengine TOS or similar service.

    Args:
        visual_service: Volcengine VisualService instance
        local_path: Path to local image file

    Returns:
        str: URL or data URL of the image

    Raises:
        Exception: If processing fails
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local image file not found: {local_path}")

    # Get file extension to determine MIME type
    _, ext = os.path.splitext(local_path)
    ext = ext.lower()

    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp'
    }

    mime_type = mime_types.get(ext, 'image/jpeg')  # default to jpeg

    try:
        # Read file and encode to base64
        with open(local_path, 'rb') as f:
            image_data = f.read()

        base64_data = base64.b64encode(image_data).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_data}"

        return data_url

    except Exception as e:
        raise Exception(f"Failed to process local image {local_path}: {e}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate images using Volcengine Jimeng API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --prompt "A beautiful landscape" --ref-image image.jpg
  %(prog)s --prompt "A sunset" --ref-image https://example.com/image.jpg --width 2048 --height 1024
  %(prog)s --prompt "Test" --access-key YOUR_KEY --secret-key YOUR_SECRET

Environment Variables:
  VOLCENGINE_ACCESS_KEY_ID    - Volcengine access key ID
  VOLCENGINE_SECRET_KEY       - Volcengine secret key
        """
    )

    parser.add_argument(
        '--prompt', '-p',
        type=str,
        required=True,
        help='Text prompt for image generation'
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
        help='Image width (will be adjusted to meet API constraints, default: 1024)'
    )

    parser.add_argument(
        '--height', '-h',
        type=int,
        default=1024,
        help='Image height (will be adjusted to meet API constraints, default: 1024)'
    )

    parser.add_argument(
        '--force-single', '-s',
        action='store_true',
        help='Force single image generation'
    )

    parser.add_argument(
        '--access-key', '-k',
        type=str,
        help='Volcengine access key ID (default: VOLCENGINE_ACCESS_KEY_ID environment variable)'
    )

    parser.add_argument(
        '--secret-key',
        type=str,
        help='Volcengine secret key (default: VOLCENGINE_SECRET_KEY environment variable)'
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

    return parser.parse_args()


def main():
    """Main function for command line usage."""
    try:
        # Parse arguments
        args = parse_arguments()

        # Get API keys from environment if not provided
        access_key = args.access_key or os.environ.get('VOLCENGINE_ACCESS_KEY_ID')
        secret = args.secret_key or os.environ.get('VOLCENGINE_SECRET_KEY')

        if not access_key or not secret:
            print("Error: Volcengine API keys required. Provide via --access-key/--secret-key or environment variables VOLCENGINE_ACCESS_KEY_ID/VOLCENGINE_SECRET_KEY", file=sys.stderr)
            sys.exit(1)

        # Initialize generator
        generator = VolcengineImageGenerator(access_key, secret)

        # Process reference images
        processed_ref_images = []
        if args.ref_image:
            for ref_image in args.ref_image:
                if ref_image.startswith(('http://', 'https://')):
                    # Already a URL
                    processed_ref_images.append(ref_image)
                else:
                    # Local file - convert to data URL
                    try:
                        url = upload_local_image(generator.visual_service, ref_image)
                        processed_ref_images.append(url)
                        print(f"Converted {ref_image} to data URL")
                    except Exception as e:
                        print(f"Error processing {ref_image}: {e}", file=sys.stderr)
                        sys.exit(1)

        # Generate image
        print(f"Generating image with prompt: '{args.prompt}'")
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

    except KeyboardInterrupt:
        print("\nOperation canceled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

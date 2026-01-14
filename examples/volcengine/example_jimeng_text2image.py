#!/usr/bin/env python3
"""
Volcengine Jimeng Text-to-Image API Example

This example demonstrates how to use the VolcengineImageGenerator to generate images
from text prompts using the Jimeng text-to-image API.

Required Setup:
1. Install dependencies: pip install -r requirements.txt
2. Configure access credentials (choose one option):

   Option A: Environment variables
   export VOLCENGINE_ACCESS_KEY_ID=your_access_key
   export VOLCENGINE_SECRET_KEY=your_secret_key

   Option B: .access.json file in project root
   {
     "platforms": {
       "volcengine": {
         "access_key_id": "your_access_key",
         "secret_key": "your_secret_key"
       }
     }
   }

Example Usage:
    python examples/volcengine/example_jimeng_text2image.py
"""

import sys
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Add the project root to Python path so we can import autostory modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from autostory.platforms.volcengine import VolcengineImageGenerator
except ImportError as e:
    print(f"Error importing VolcengineImageGenerator: {e}")
    print("Make sure you're running this from the project root and all dependencies are installed.")
    sys.exit(1)


def download_images(image_urls, output_dir=None):
    """
    Download images from URLs and save them to the specified directory.

    Args:
        image_urls: List of image URLs to download
        output_dir: Directory to save images (default: generated_images/ under script's parent dir)

    Returns:
        list: List of paths to saved image files
    """
    if output_dir is None:
        # Default to a generated_images subdirectory under the script's parent directory
        script_parent = Path(__file__).resolve().parent
        output_dir = script_parent / "generated_images"

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []

    for i, url in enumerate(image_urls, 1):
        try:
            print(f"📥 Downloading image {i}/{len(image_urls)}...")

            # Generate filename with timestamp and index
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_image_{timestamp}_{i}.jpg"
            filepath = output_dir / filename

            # Download the image
            with urllib.request.urlopen(url, timeout=30) as response:
                image_data = response.read()

            # Save to file
            with open(filepath, 'wb') as f:
                f.write(image_data)

            saved_paths.append(filepath)
            print(f"✅ Saved to: {filepath}")

        except urllib.error.URLError as e:
            print(f"❌ Failed to download image {i}: URL error - {e}")
        except Exception as e:
            print(f"❌ Failed to download image {i}: {e}")

    return saved_paths


def main():
    """Main example function demonstrating Volcengine Jimeng text-to-image generation."""

    # Sample jimeng_play_writer in Chinese: "The Jin army is attacking, Northern Song Dynasty Bianjing, crowded with people"
    prompt = "金军来袭，北宋汴京，人来人往"

    # Optional: Reference images (URLs or local file paths)
    reference_images = [
        # You can add reference image URLs here, for example:
        # "https://example.com/reference-image.jpg",
        # "./local-reference-image.png"
    ]

    # Generation parameters
    generation_params = {
        "width": 1024,              # Image width (will be adjusted to API constraints)
        "height": 1024,             # Image height (will be adjusted to API constraints)
        "force_single": True,      # Whether to force single image generation
        "max_retries": 15,          # Maximum polling attempts
        "polling_interval": 4       # Seconds between polling attempts
    }

    print("🎨 Volcengine Jimeng Text-to-Image Generation Example")
    print("=" * 60)
    print(f"Prompt: {prompt}")
    print(f"Dimensions: {generation_params['width']}x{generation_params['height']}")
    print(f"Reference images: {len(reference_images)} provided")
    print()

    try:
        # Initialize the Volcengine image generator
        # This will automatically get credentials from environment variables or .access.json
        print("🔧 Initializing Volcengine Image Generator...")
        generator = VolcengineImageGenerator()

        # Generate the image
        print("🚀 Starting image generation...")
        print("This may take 30-60 seconds depending on server load.")

        result = generator.generate(
            prompt=prompt,
            image_urls=reference_images if reference_images else None,
            **generation_params
        )

        # Display results
        print("\n✅ Generation completed successfully!")
        print("-" * 40)
        print(f"Task ID: {result['task_id']}")
        print(f"Generated images: {len(result['image_urls'])}")

        if result['image_urls']:
            print("\n📸 Generated Image URLs:")
            for i, url in enumerate(result['image_urls'], 1):
                print(f"  {i}. {url}")

            # Download and save images to local directory
            print("\n💾 Downloading and saving images...")
            saved_paths = download_images(result['image_urls'])

            if saved_paths:
                print(f"\n✅ Successfully saved {len(saved_paths)} image(s) to local directory:")
                images_dir = Path(__file__).resolve().parent / "generated_images"
                print(f"📁 Location: {images_dir}")
                for path in saved_paths:
                    print(f"  📄 {path.name}")
                print("\n💡 Tip: Images have been saved locally for offline viewing.")
            else:
                print("\n⚠️  Warning: No images were successfully downloaded and saved.")

        else:
            print("⚠️  No image URLs returned. This might indicate an issue with the generation.")

    except KeyboardInterrupt:
        print("\n⏹️  Generation interrupted by user.")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error during image generation: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("1. Check that your API credentials are configured correctly")
        print("2. Verify that the 'volcengine' Python package is installed")
        print("3. Ensure you have a stable internet connection")
        print("4. Check the Volcengine service status")
        sys.exit(1)


def demonstrate_parameter_options():
    """Demonstrate different parameter options for image generation."""

    print("\n🔧 Parameter Options Demonstration")
    print("=" * 50)

    # Example 1: High resolution image
    print("📐 High Resolution Example:")
    print("  Width: 2048, Height: 2048")
    print("  Prompt: 'A futuristic cityscape at sunset'")

    # Example 2: With reference image
    print("\n🖼️  With Reference Image Example:")
    print("  Reference: 'path/to/style-reference.jpg'")
    print("  Prompt: 'Portrait in the style of the reference image'")

    # Example 3: Force single image
    print("\n🎯 Force Single Image Example:")
    print("  force_single: True")
    print("  Result: Only one image will be generated")

    print("\n📚 For more examples, see the VolcengineImageGenerator class documentation.")


if __name__ == "__main__":
    # Check if user wants to see parameter examples
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', '--examples']:
        demonstrate_parameter_options()
    else:
        main()

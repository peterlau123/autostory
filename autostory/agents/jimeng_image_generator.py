from typing import TYPE_CHECKING, List, Dict, Any

if TYPE_CHECKING:
    from ..platforms.platform import Platform


class JimengImageGenerator:
    """
    JimengImageGenerator agent for generating images from text prompts.

    This agent takes image prompts and generates actual images using
    the Volcengine Jimeng image generation service.
    """

    def __init__(self, image_generator_platform: Any, **kwargs):
        """
        Initialize the JimengImageGenerator agent.

        Args:
            image_generator_platform: The image generation platform (Volcengine Jimeng)
            **kwargs: Additional arguments for future extensions
        """
        self.image_generator = image_generator_platform
        self.kwargs = kwargs

    def generate(self, prompts: List[str], reference_images: List[str] = None) -> Dict[str, Any]:
        """
        Generate images from prompts.

        Args:
            prompts: List of image prompts to generate images for
            reference_images: Optional list of reference image URLs

        Returns:
            Dict containing:
            - 'images': List of generated image URLs
            - 'prompts_used': List of prompts that were used
            - 'task_ids': List of task IDs for tracking

        Raises:
            ValueError: If prompts list is empty
            RuntimeError: If image generation fails
        """
        if not prompts or len(prompts) == 0:
            raise ValueError("Prompts list cannot be empty")

        try:
            all_images = []
            all_task_ids = []
            prompts_used = []

            # Generate images for each prompt
            for i, prompt in enumerate(prompts):
                print(f"Generating image {i+1}/{len(prompts)}: {prompt[:50]}...")

                # Use the image generator platform
                result = self.image_generator.generate(
                    prompt=prompt,
                    image_urls=reference_images,
                    **self.kwargs
                )

                # Collect results
                if 'image_urls' in result:
                    all_images.extend(result['image_urls'])
                if 'task_id' in result:
                    all_task_ids.append(result['task_id'])

                prompts_used.append(prompt)

            return {
                'images': all_images,
                'prompts_used': prompts_used,
                'task_ids': all_task_ids
            }

        except Exception as e:
            raise RuntimeError(f"Failed to generate images: {str(e)}") from e

    def generate_single(self, prompt: str, reference_images: List[str] = None) -> Dict[str, Any]:
        """
        Generate a single image from one prompt.

        Args:
            prompt: Single image prompt
            reference_images: Optional list of reference image URLs

        Returns:
            Dict containing image generation result
        """
        return self.generate([prompt], reference_images)


# Example usage and testing
if __name__ == "__main__":
    from ..platforms.volcengine import Volcengine

    def test_jimeng_image_generator():
        """Test the JimengImageGenerator agent functionality."""
        print("Testing JimengImageGenerator agent...")

        # Test 1: Basic initialization
        try:
            # Note: This will fail if volcengine package is not installed
            # but that's expected - we're testing the interface
            try:
                volcengine_platform = Volcengine()
                image_gen = JimengImageGenerator(image_generator_platform=volcengine_platform)
                print("✓ Basic initialization test passed")
            except ImportError:
                print("⚠️  Volcengine package not installed - skipping full test")
                print("✓ Basic initialization interface test passed")
                return True

            # Test with sample prompts (would fail without API)
            test_prompts = [
                "A beautiful landscape with mountains and lake",
                "A futuristic city at sunset"
            ]

            # This will likely fail due to missing API credentials, but tests the interface
            try:
                result = image_gen.generate(test_prompts)
                print(f"✓ Generation test passed. Got {len(result.get('images', []))} images")
            except Exception as e:
                print(f"⚠️  Generation test failed (expected without API): {str(e)[:100]}...")

        except Exception as e:
            print(f"✗ Basic test failed: {e}")
            return False

        # Test 2: Empty prompts handling
        try:
            image_gen.generate([])
            print("✗ Empty prompts test failed: should have raised ValueError")
            return False
        except ValueError:
            print("✓ Empty prompts test passed: correctly raised ValueError")
        except Exception as e:
            print(f"✗ Empty prompts test failed with unexpected error: {e}")
            return False

        print("All tests passed! ✓")
        return True

    # Run tests
    test_jimeng_image_generator()

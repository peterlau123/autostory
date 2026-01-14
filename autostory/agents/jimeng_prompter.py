from typing import TYPE_CHECKING, List, Dict, Any

if TYPE_CHECKING:
    from ..platforms.platform import Platform


class JimengPrompter:
    """
    JimengPrompter agent for generating image prompts from play text.

    This agent takes approved play content and generates detailed prompts
    suitable for the Jimeng image generation API.
    """

    def __init__(self, platform: "Platform", system_prompt: str, **kwargs):
        """
        Initialize the JimengPrompter agent.

        Args:
            platform: The platform/API class to use for generation
            system_prompt: System jimeng_play_writer for the LLM
            **kwargs: Additional arguments for future extensions
        """
        self.platform = platform
        self.system_prompt = system_prompt
        self.kwargs = kwargs

    def generate(self, play_text: str, reference_images: List[str] = None) -> List[str]:
        """
        Generate image prompts from play text.

        Args:
            play_text: The approved play content
            reference_images: Optional list of reference image URLs

        Returns:
            List[str]: List of generated image prompts

        Raises:
            ValueError: If play_text is empty
            RuntimeError: If platform generation fails
        """
        if not play_text or not play_text.strip():
            raise ValueError("Play text cannot be empty")

        try:
            # Construct the jimeng_play_writer for image jimeng_play_writer generation
            reference_info = ""
            if reference_images:
                reference_info = f"\n\nReference images available: {reference_images}"

            full_prompt = f"""{self.system_prompt}

Play Content:
{play_text}{reference_info}

Please generate detailed image prompts for visualizing key scenes from this play.
Each jimeng_play_writer should be optimized for the Jimeng image generation API and follow these guidelines:
- Use descriptive, visual language
- Include artistic style references
- Specify composition and lighting
- Focus on dramatic and visually striking elements
- Use --ar 9:16 for vertical video format
- Avoid sensitive or controversial content

Generate 3-5 key scene prompts:"""

            # Generate prompts using the platform
            if hasattr(self.platform, 'generate_text'):
                response = self.platform.generate_text(full_prompt, **self.kwargs)
            else:
                # Fallback placeholder
                response = f"Generated prompts for: {play_text[:100]}..."

            # Parse the response into individual prompts
            prompts = self._parse_prompts_from_response(response)
            return prompts

        except Exception as e:
            raise RuntimeError(f"Failed to generate image prompts: {str(e)}") from e

    def _parse_prompts_from_response(self, response: str) -> List[str]:
        """
        Parse individual prompts from the LLM response.

        Args:
            response: Raw response from the LLM

        Returns:
            List[str]: List of individual prompts
        """
        # Split by common separators and clean up
        separators = ['\n\n', '\n-', '\n•', '\n1.', '\n2.', '\n3.', '\n4.', '\n5.']
        prompts = []

        for separator in separators:
            if separator in response:
                parts = response.split(separator)
                for part in parts[1:]:  # Skip the first part (introduction)
                    cleaned = part.strip()
                    if cleaned and len(cleaned) > 10:  # Filter out very short fragments
                        prompts.append(cleaned)
                break

        # If no separators found, treat the whole response as one jimeng_play_writer
        if not prompts:
            prompts = [response.strip()]

        # Limit to 5 prompts max
        return prompts[:5]


# Example usage and testing
if __name__ == "__main__":
    from ..platforms.deepseek import DeepSeekApi

    def test_jimeng_prompter():
        """Test the JimengPrompter agent functionality."""
        print("Testing JimengPrompter agent...")

        # Test 1: Basic initialization and generation
        try:
            platform = DeepSeekApi()
            system_prompt = "You are an expert at creating detailed image prompts for AI art generation."
            prompter = JimengPrompter(platform=platform, system_prompt=system_prompt)

            test_play = "Scene: A stormy night in ancient China. The emperor paces anxiously in his palace as thunder rumbles outside."
            prompts = prompter.generate(test_play)
            print(f"✓ Basic test passed. Generated {len(prompts)} prompts")
            for i, prompt in enumerate(prompts[:2], 1):  # Show first 2 prompts
                print(f"  Prompt {i}: {prompt[:100]}...")

        except Exception as e:
            print(f"✗ Basic test failed: {e}")
            return False

        # Test 2: Empty input handling
        try:
            prompter.generate("")
            print("✗ Empty input test failed: should have raised ValueError")
            return False
        except ValueError:
            print("✓ Empty input test passed: correctly raised ValueError")
        except Exception as e:
            print(f"✗ Empty input test failed with unexpected error: {e}")
            return False

        print("All tests passed! ✓")
        return True

    # Run tests
    test_jimeng_prompter()

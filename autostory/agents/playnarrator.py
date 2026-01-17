from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..platforms.platform import Platform


class PlayNarrator:
    """
    PlayNarrator agent for converting story scripts into narration scripts suitable for voice-over/broadcasting.
    """

    def __init__(self, platform: "Platform", system_prompt: str, **kwargs):
        """
        Initialize the PlayNarrator agent.

        Args:
            platform: The platform/API class to use for generation
            system_prompt: System prompt for the LLM
            **kwargs: Additional arguments for future extensions
        """
        self.platform = platform
        self.system_prompt = system_prompt
        self.kwargs = kwargs

    def generate(self, story_script: str) -> str:
        """
        Convert a story script into a narration script for voice-over/broadcasting.

        Args:
            story_script: The completed story script to convert

        Returns:
            str: Narration script suitable for voice-over

        Raises:
            ValueError: If input script is empty
            RuntimeError: If platform generation fails
        """
        if not story_script or not story_script.strip():
            raise ValueError("Story script cannot be empty")

        try:
            # Construct the full prompt with system prompt and story script
            full_prompt = f"{self.system_prompt}\n\nStory Script to Convert:\n{story_script}\n\nConvert to narration script:"

            # Check if platform has generate_text method
            if hasattr(self.platform, 'generate_text'):
                return self.platform.generate_text(full_prompt, **self.kwargs)
            else:
                # Fallback placeholder for platforms without generate_text
                return f"Narration script from: {story_script[:100]}... (using system prompt: {self.system_prompt})"
        except Exception as e:
            raise RuntimeError(f"Failed to generate narration script: {str(e)}") from e


# Example usage and testing
if __name__ == "__main__":
    from ..platforms.deepseek import DeepSeekApi

    def test_playnarrator():
        """Test the PlayNarrator agent functionality."""
        print("Testing PlayNarrator agent...")

        # Test 1: Basic initialization and generation
        try:
            platform = DeepSeekApi()
            system_prompt = "You are a professional narrator. Convert story scripts into engaging voice-over narration."
            playnarrator = PlayNarrator(platform=platform, system_prompt=system_prompt)

            test_script = """
            Scene 1: The hero stands at the edge of the cliff.

            HERO: I must make this leap of faith!

            NARRATOR: The wind howls as our hero contemplates his destiny.
            """
            output = playnarrator.generate(test_script)
            print("✓ Basic test passed.")
            print(f"  Input length: {len(test_script)} characters")
            print(f"  Output: {output[:100]}..." if len(output) > 100 else f"  Output: {output}")

        except Exception as e:
            print(f"✗ Basic test failed: {e}")
            return False

        # Test 2: Empty input handling
        try:
            playnarrator.generate("")
            print("✗ Empty input test failed: should have raised ValueError")
            return False
        except ValueError:
            print("✓ Empty input test passed: correctly raised ValueError")
        except Exception as e:
            print(f"✗ Empty input test failed with unexpected error: {e}")
            return False

        # Test 3: Whitespace input handling
        try:
            playnarrator.generate("   ")
            print("✗ Whitespace input test failed: should have raised ValueError")
            return False
        except ValueError:
            print("✓ Whitespace input test passed: correctly raised ValueError")
        except Exception as e:
            print(f"✗ Whitespace input test failed with unexpected error: {e}")
            return False

        print("All tests passed! ✓")
        return True

    # Run tests
    test_playnarrator()

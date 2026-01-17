from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..platforms.platform import Platform


class PlayCritic:
    """
    PlayCritic agent for critiquing and analyzing plays from text input.
    """

    def __init__(self, platform: "Platform", system_prompt: str, **kwargs):
        """
        Initialize the PlayCritic agent.

        Args:
            platform: The platform/API class to use for generation
            system_prompt: System jimeng_play_writer for the LLM
            **kwargs: Additional arguments for future extensions
        """
        self.platform = platform
        self.system_prompt = system_prompt
        self.kwargs = kwargs

    def generate(self, text: str) -> str:
        """
        Generate critique/analysis of the input text.

        Args:
            text: Input text to critique/analyze

        Returns:
            str: Generated critique/analysis text

        Raises:
            ValueError: If input text is empty
            RuntimeError: If platform generation fails
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        try:
            # Construct the full jimeng_play_writer with system jimeng_play_writer and user input
            full_prompt = f"{self.system_prompt}\n\nInput: {text}\n\nProvide a detailed critique and analysis:"

            # Check if platform has generate_text method
            if hasattr(self.platform, 'generate_text'):
                return self.platform.generate_text(full_prompt, **self.kwargs)
            else:
                # Fallback placeholder for platforms without generate_text
                return f"Critique of: {text} (using system jimeng_play_writer: {self.system_prompt})"
        except Exception as e:
            raise RuntimeError(f"Failed to generate critique: {str(e)}") from e


# Example usage and testing
if __name__ == "__main__":
    from ..platforms.deepseek import DeepSeekApi

    def test_playcritic():
        """Test the PlayCritic agent functionality."""
        print("Testing PlayCritic agent...")

        # Test 1: Basic initialization and generation
        try:
            platform = DeepSeekApi()
            system_prompt = "You are a professional play critic. Provide detailed analysis and constructive feedback on plays and scripts."
            playcritic = PlayCritic(platform=platform, system_prompt=system_prompt)

            test_input = "A short play about a family dinner that goes wrong"
            output = playcritic.generate(test_input)
            print(f"✓ Basic test passed. Input: '{test_input}'")
            print(f"  Output: {output[:100]}..." if len(output) > 100 else f"  Output: {output}")

        except Exception as e:
            print(f"✗ Basic test failed: {e}")
            return False

        # Test 2: Empty input handling
        try:
            playcritic.generate("")
            print("✗ Empty input test failed: should have raised ValueError")
            return False
        except ValueError:
            print("✓ Empty input test passed: correctly raised ValueError")
        except Exception as e:
            print(f"✗ Empty input test failed with unexpected error: {e}")
            return False

        # Test 3: Whitespace input handling
        try:
            playcritic.generate("   ")
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
    test_playcritic()

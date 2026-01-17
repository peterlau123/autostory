"""
Jimeng Story Workflow

This module implements a LangGraph-based workflow for generating stories with images.
The workflow orchestrates multiple AI agents to create and refine plays, then generate
visual content using the Jimeng image generation service.

Workflow Steps:
1. Playwriter creates initial play from user input
2. Playcritic reviews and critiques the play
3. If approved: proceed to image generation
4. If not approved: Playwriter revises and loop continues
5. Approved play goes to JimengPrompter for image generation
6. Generated prompts go to JimengImageGenerator for final images
7. Optional: PlayNarrator converts story to narration script for voice-over
"""

from typing import TypedDict, List, Dict, Any, Optional
import argparse
import os
import base64
from urllib.parse import urlparse
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from ..agents.playwriter import Playwriter
from ..agents.playcritic import PlayCritic
from ..agents.jimeng_prompter import JimengPrompter
from ..agents.jimeng_image_generator import JimengImageGenerator
from ..agents.playnarrator import PlayNarrator
from ..platforms.deepseek import DeepSeekApi
from ..platforms.volcengine import Volcengine

from utils import PromptReader

class WorkflowState(TypedDict):
    """State structure for the Jimeng story workflow."""

    # Input
    user_input: str
    reference_images: List[str]

    # Play creation and refinement
    current_play: str
    critique_feedback: str
    revision_count: int
    max_revisions: int
    approved: bool
    final_approved_play: str

    # Image generation
    image_prompts: List[str]
    generated_images: List[str]
    task_ids: List[str]

    # Narration
    narration_script: str

    # Status and errors
    status: str
    error_message: Optional[str]


class JimengStoryWorkflow:
    """
    LangGraph-based workflow for generating stories with images.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the workflow with agents and configuration.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.max_revisions = self.config.get('max_revisions', 3)

        # Narration configuration
        self.generate_narration = self.config.get('generate_narration', True)

        # Initialize platforms
        self.text_platform = DeepSeekApi()
        self.image_platform = Volcengine()

        # Initialize agents
        self._init_agents()

        # Build the workflow graph
        self.graph = self._build_graph()

    def _init_agents(self):
        """Initialize all agents with appropriate configurations."""
        # Playwriter agent
        playwriter_prompt = PromptReader('autostory/prompts/jimeng_play_writer').read()
        self.playwriter = Playwriter(
            platform=self.text_platform,
            system_prompt=playwriter_prompt
        )

        # Playcritic agent
        critic_prompt = PromptReader('autostory/prompts/jimeng_play_critic').read()
        self.playcritic = PlayCritic(
            platform=self.text_platform,
            system_prompt=critic_prompt
        )

        # Jimeng prompter agent
        prompter_prompt = PromptReader('autostory/prompts/jimeng_image_prompter').read()
        self.jimeng_prompter = JimengPrompter(
            platform=self.text_platform,
            system_prompt=prompter_prompt
        )

        # PlayNarrator agent (only initialize if narration is enabled)
        if self.generate_narration:
            narrator_prompt = PromptReader('autostory/prompts/jimeng_play_narration').read()
            self.play_narrator = PlayNarrator(
                platform=self.text_platform,
                system_prompt=narrator_prompt
            )
        else:
            self.play_narrator = None

        # Jimeng image generator agent (with error handling for missing volcengine)
        try:
            self.jimeng_image_generator = JimengImageGenerator(
                image_generator_platform=self.image_platform.jimeng_generator
            )
            self.image_generation_available = True
        except ImportError:
            self.jimeng_image_generator = None
            self.image_generation_available = False

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create the graph
        workflow = StateGraph(WorkflowState)

        # Add nodes
        workflow.add_node("write_initial_play", self._write_initial_play)
        workflow.add_node("critique_play", self._critique_play)
        workflow.add_node("revise_play", self._revise_play)
        workflow.add_node("generate_image_prompts", self._generate_image_prompts)
        workflow.add_node("generate_images", self._generate_images)

        # Add narration node if narration is enabled
        if self.generate_narration:
            workflow.add_node("generate_narration", self._generate_narration)

        # Set entry point
        workflow.set_entry_point("write_initial_play")

        # Add edges
        workflow.add_edge("write_initial_play", "critique_play")
        workflow.add_edge("revise_play", "critique_play")

        # Add conditional edges for approval loop
        workflow.add_conditional_edges(
            "critique_play",
            self._should_revise,
            {
                "revise": "revise_play",
                "approved": "generate_image_prompts"
            }
        )

        workflow.add_edge("generate_image_prompts", "generate_images")

        # Add narration edge if enabled
        if self.generate_narration:
            workflow.add_edge("generate_images", "generate_narration")
            workflow.add_edge("generate_narration", END)
        else:
            workflow.add_edge("generate_images", END)

        return workflow.compile()

    def _write_initial_play(self, state: WorkflowState) -> Dict[str, Any]:
        """Write the initial play from user input."""
        try:
            play = self.playwriter.generate(state["user_input"])
            return {
                "current_play": play,
                "revision_count": 0,
                "status": "play_written"
            }
        except Exception as e:
            return {
                "error_message": f"Failed to write initial play: {str(e)}",
                "status": "error"
            }

    def _critique_play(self, state: WorkflowState) -> Dict[str, Any]:
        """Critique the current play."""
        try:
            critique_prompt = f"""Please critique this play:

{state["current_play"]}

Revision count: {state["revision_count"]}/{self.max_revisions}

If the play is ready for production and image generation, respond with APPROVED and provide the final polished version of the play.
If the play needs revision, respond with NEEDS_REVISION and provide specific feedback for improvement."""

            critique = self.playcritic.generate(critique_prompt)

            # Check if approved
            approved = "APPROVED" in critique.upper()

            # Extract final play if approved
            final_play = state["current_play"]
            if approved:
                # If approved, extract the final polished play from the critique response
                # The critique should contain the final approved version
                final_play = critique  # For now, use the full response as the final play

            return {
                "critique_feedback": critique,
                "approved": approved,
                "final_play": final_play if approved else state["current_play"],
                "status": "play_critiqued"
            }
        except Exception as e:
            return {
                "error_message": f"Failed to critique play: {str(e)}",
                "status": "error"
            }

    def _should_revise(self, state: WorkflowState) -> str:
        """Determine if the play should be revised or is approved."""
        if state.get("error_message"):
            return END  # Stop on error

        if state["approved"]:
            return "approved"

        if state["revision_count"] >= self.max_revisions:
            # Max revisions reached, proceed anyway
            return "approved"

        return "revise"

    def _revise_play(self, state: WorkflowState) -> Dict[str, Any]:
        """Revise the play based on critique feedback."""
        try:
            revision_prompt = f"""Please revise this play based on the following critique:

Original Play:
{state["current_play"]}

Critique:
{state["critique_feedback"]}

Revision count: {state["revision_count"] + 1}/{self.max_revisions}

Please create an improved version addressing the critique points."""

            revised_play = self.playwriter.generate(revision_prompt)

            return {
                "current_play": revised_play,
                "revision_count": state["revision_count"] + 1,
                "status": "play_revised"
            }
        except Exception as e:
            return {
                "error_message": f"Failed to revise play: {str(e)}",
                "status": "error"
            }

    def _generate_image_prompts(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate image prompts from the approved play."""
        try:
            # Use final approved play if available, otherwise use current play
            approved_play = state.get("final_approved_play") or state["current_play"]
            prompts = self.jimeng_prompter.generate(
                approved_play,
                state.get("reference_images")
            )
            return {
                "image_prompts": prompts,
                "status": "prompts_generated"
            }
        except Exception as e:
            return {
                "error_message": f"Failed to generate image prompts: {str(e)}",
                "status": "error"
            }

    def _generate_images(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate images from the prompts."""
        if not self.image_generation_available:
            return {
                "generated_images": [],
                "task_ids": [],
                "status": "completed",  # Still mark as completed, just without images
                "error_message": "Image generation not available (volcengine package not installed)"
            }

        try:
            result = self.jimeng_image_generator.generate(
                state["image_prompts"],
                state.get("reference_images")
            )

            return {
                "generated_images": result.get("images", []),
                "task_ids": result.get("task_ids", []),
                "status": "completed"
            }
        except Exception as e:
            return {
                "error_message": f"Failed to generate images: {str(e)}",
                "status": "error"
            }

    def _generate_narration(self, state: WorkflowState) -> Dict[str, Any]:
        """Generate narration script from the completed play."""
        try:
            # Use final approved play if available, otherwise use current play
            approved_play = state.get("final_approved_play") or state["current_play"]
            narration_script = self.play_narrator.generate(approved_play)
            return {
                "narration_script": narration_script,
                "status": "completed"
            }
        except Exception as e:
            return {
                "error_message": f"Failed to generate narration script: {str(e)}",
                "status": "error"
            }

    def run(self, user_input: str, reference_images: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run the complete workflow.

        Args:
            user_input: The user's story jimeng_play_writer
            reference_images: Optional list of reference image URLs

        Returns:
            Dict containing the final results
        """
        initial_state = {
            "user_input": user_input,
            "reference_images": reference_images or [],
            "current_play": "",
            "critique_feedback": "",
            "revision_count": 0,
            "max_revisions": self.max_revisions,
            "approved": False,
            "final_approved_play": "",
            "image_prompts": [],
            "generated_images": [],
            "task_ids": [],
            "status": "starting",
            "error_message": None
        }

        try:
            # Run the workflow
            final_state = self.graph.invoke(initial_state)

            # Return the results
            # Use final approved play if available, otherwise use current play
            final_play = final_state.get("final_approved_play") or final_state.get("current_play")
            results = {
                "success": final_state.get("status") == "completed",
                "play": final_play,
                "revisions": final_state.get("revision_count"),
                "critique": final_state.get("critique_feedback"),
                "image_prompts": final_state.get("image_prompts"),
                "generated_images": final_state.get("generated_images"),
                "task_ids": final_state.get("task_ids"),
                "status": final_state.get("status"),
                "error": final_state.get("error_message")
            }

            # Add narration if generated
            if self.generate_narration and final_state.get("narration_script"):
                results["narration_script"] = final_state.get("narration_script")

            return results

        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "status": "failed"
            }


def process_image_references(image_paths: List[str]) -> List[str]:
    """
    Process image references, converting local files to base64 data URLs.

    Args:
        image_paths: List of image paths (URLs or local file paths)

    Returns:
        List of processed image references (URLs or base64 data URLs)
    """
    processed_images = []

    for image_path in image_paths:
        # Check if it's a URL
        parsed = urlparse(image_path)
        if parsed.scheme and parsed.netloc:
            # It's already a URL, use as-is
            processed_images.append(image_path)
        else:
            # It's a local file path
            if os.path.isfile(image_path):
                try:
                    # Read the file and convert to base64
                    with open(image_path, 'rb') as f:
                        file_data = f.read()

                    # Get file extension to determine MIME type
                    _, ext = os.path.splitext(image_path)
                    ext = ext.lower()

                    mime_type = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.gif': 'image/gif',
                        '.webp': 'image/webp'
                    }.get(ext, 'image/jpeg')  # Default to jpeg

                    # Convert to base64 data URL
                    base64_data = base64.b64encode(file_data).decode('utf-8')
                    data_url = f"data:{mime_type};base64,{base64_data}"
                    processed_images.append(data_url)

                except Exception as e:
                    print(f"Warning: Failed to process local image file '{image_path}': {e}")
                    # Skip this file but continue with others
            else:
                print(f"Warning: Local image file '{image_path}' not found, skipping")
                # Skip missing files but continue with others

    return processed_images


# Convenience function for easy usage
def generate_jimeng_story(user_input: str, reference_images: Optional[List[str]] = None,
                         config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate a complete story with images using the Jimeng workflow.

    Args:
        user_input: The user's story jimeng_play_writer
        reference_images: Optional list of reference image URLs
        config: Optional workflow configuration

    Returns:
        Dict containing the complete results
    """
    workflow = JimengStoryWorkflow(config)
    return workflow.run(user_input, reference_images)


def main():
    """CLI entry point for the Jimeng Story Workflow."""
    parser = argparse.ArgumentParser(
        description="Generate stories with images using the Jimeng workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python jimeng_story.py "Create a play about the Battle of Red Cliffs"
  python jimeng_story.py "Tell a story about ancient Chinese warriors" --images "https://example.com/warrior.jpg"
  python jimeng_story.py "Historical drama" --max-revisions 5
  python jimeng_story.py "Epic tale" --generate-narration
        """
    )

    parser.add_argument(
        "user_input",
        help="The story prompt or description"
    )

    parser.add_argument(
        "--images", "-i",
        nargs="*",
        default=[],
        help="Reference images (URLs or local file paths, can specify multiple)"
    )

    parser.add_argument(
        "--max-revisions", "-r",
        type=int,
        default=3,
        help="Maximum number of revisions allowed (default: 3)"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output"
    )

    parser.add_argument(
        "--no-narration",
        action="store_true",
        help="Disable narration script generation (narration is enabled by default)"
    )

    args = parser.parse_args()

    # Prepare configuration
    config = {
        "max_revisions": args.max_revisions,
        "generate_narration": not args.no_narration  # Default to True, False only if --no-narration is specified
    }

    if not args.quiet:
        print("🎭 Starting Jimeng Story Generation Workflow")
        print("=" * 60)
        print(f"Prompt: {args.user_input}")
        if args.images:
            print(f"Reference Images: {len(args.images)} provided")
        narration_enabled = not args.no_narration
        if narration_enabled:
            print("Narration: Will generate narration script (default)")
        else:
            print("Narration: Disabled")
        print()

    # Process image references (convert local files to base64 data URLs)
    processed_images = process_image_references(args.images)

    # Run the workflow
    result = generate_jimeng_story(args.user_input, processed_images, config)

    if result["success"]:
        if not args.quiet:
            print("✅ Workflow completed successfully!")
            print(f"📝 Final Play ({result['revisions']} revisions):")
            print("-" * 40)
            print(result["play"][:500] + "..." if len(result["play"]) > 500 else result["play"])
            print()

            if result["critique"]:
                print(f"🎭 Final Critique:")
                print(result["critique"][:300] + "..." if len(result["critique"]) > 300 else result["critique"])
                print()

            if result["image_prompts"]:
                print(f"🎨 Generated {len(result['image_prompts'])} Image Prompts:")
                for i, prompt in enumerate(result["image_prompts"], 1):
                    print(f"  {i}. {prompt[:100]}...")
                print()

            if result["generated_images"]:
                print(f"🖼️  Generated {len(result['generated_images'])} Images:")
                for i, url in enumerate(result["generated_images"], 1):
                    print(f"  {i}. {url}")
                print()

            if result["task_ids"]:
                print(f"📋 Task IDs: {result['task_ids']}")

            if result.get("narration_script"):
                print(f"🎙️  Narration Script:")
                print("-" * 40)
                print(result["narration_script"][:800] + "..." if len(result["narration_script"]) > 800 else result["narration_script"])
                print()
        else:
            # Quiet mode: just print summary
            print(f"Success: Generated play with {result['revisions']} revisions")
            if result["generated_images"]:
                print(f"Generated {len(result['generated_images'])} images")
            if result.get("narration_script"):
                print("Narration script generated")

    else:
        error_msg = result.get('error', 'Unknown error')
        if args.quiet:
            print(f"Failed: {error_msg}")
        else:
            print(f"❌ Workflow failed: {error_msg}")
            print(f"📊 Final status: {result.get('status', 'unknown')}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

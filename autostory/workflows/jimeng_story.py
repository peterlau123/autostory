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
5. Approved play goes to JimengPrompter for image jimeng_play_writer generation
6. Generated prompts go to JimengImageGenerator for final images
"""

from typing import TypedDict, List, Dict, Any, Optional
import argparse
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from ..agents.playwriter import Playwriter
from ..agents.playcritic import PlayCritic
from ..agents.jimeng_prompter import JimengPrompter
from ..agents.jimeng_image_generator import JimengImageGenerator
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

    # Image generation
    image_prompts: List[str]
    generated_images: List[str]
    task_ids: List[str]

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

Provide your analysis and clearly state APPROVED if the play is ready for image generation, or NEEDS_REVISION if it requires changes."""

            critique = self.playcritic.generate(critique_prompt)

            # Check if approved
            approved = "APPROVED" in critique.upper() and "NEEDS_REVISION" not in critique.upper()

            return {
                "critique_feedback": critique,
                "approved": approved,
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
            prompts = self.jimeng_prompter.generate(
                state["current_play"],
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
            return {
                "success": final_state.get("status") == "completed",
                "play": final_state.get("current_play"),
                "revisions": final_state.get("revision_count"),
                "critique": final_state.get("critique_feedback"),
                "image_prompts": final_state.get("image_prompts"),
                "generated_images": final_state.get("generated_images"),
                "task_ids": final_state.get("task_ids"),
                "status": final_state.get("status"),
                "error": final_state.get("error_message")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution failed: {str(e)}",
                "status": "failed"
            }


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
        help="Reference image URLs (can specify multiple)"
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

    args = parser.parse_args()

    # Prepare configuration
    config = {
        "max_revisions": args.max_revisions
    }

    if not args.quiet:
        print("🎭 Starting Jimeng Story Generation Workflow")
        print("=" * 60)
        print(f"Prompt: {args.user_input}")
        if args.images:
            print(f"Reference Images: {len(args.images)} provided")
        print()

    # Run the workflow
    result = generate_jimeng_story(args.user_input, args.images, config)

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
        else:
            # Quiet mode: just print summary
            print(f"Success: Generated play with {result['revisions']} revisions")
            if result["generated_images"]:
                print(f"Generated {len(result['generated_images'])} images")

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

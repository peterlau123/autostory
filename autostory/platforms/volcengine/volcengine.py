#!/usr/bin/env python3
"""
Volcengine Jimeng Text-to-Image Module

This module provides Volcengine Jimeng API integration for text-to-image generation.

Example usage:
    from autostory.platforms.volcengine import VolcengineImageGenerator

    generator = VolcengineImageGenerator(access_key_id="your_key", secret_key="your_secret")
    result = generator.generate("A beautiful landscape", width=1024, height=1024)
    print(result["image_urls"])
"""

import time
import json
from typing import Optional, List, Dict, Any
from volcengine.visual.VisualService import VisualService

from .. import get_access_config


class VolcengineImageGenerator:
    """
    Volcengine Jimeng Text-to-Image Generator Class

    Handles text-to-image generation using Volcengine Jimeng API.
    """

    def __init__(self, access_key_id: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Initialize Volcengine Image Generator instance.

        Args:
            access_key_id: Volcengine access key ID. If None, uses access configuration.
            secret_key: Volcengine secret key. If None, uses access configuration.
        """
        if access_key_id is None or secret_key is None:
            # Get configuration using the access config system
            config = get_access_config('volcengine')
            self.access_key_id = access_key_id or config['access_key_id']
            self.secret_key = secret_key or config['secret_key']
        else:
            self.access_key_id = access_key_id
            self.secret_key = secret_key

        self.visual_service = VisualService()
        self.visual_service.set_ak(self.access_key_id)
        self.visual_service.set_sk(self.secret_key)

    @staticmethod
    def fix_dimension(width: int = 1024, height: int = 1024) -> tuple[int, int]:
        """
        Fix dimensions to meet API requirements.

        Width*height must be in [1024*1024, 4096*4096], and aspect ratio in [1/16, 16).

        Args:
            width: Desired width
            height: Desired height

        Returns:
            tuple: (fixed_width, fixed_height)
        """
        if width * height < 1024 * 1024:
            return 1024, 1024
        if 4096 * 4096 < width * height:
            return 4096, 4096
        ratio = width * 1.0 / height

        min_ratio = 1 / 16
        max_ratio = 16
        new_w, new_h = width, height
        if ratio < min_ratio:
            new_w, new_h = min_ratio * height, height
        if max_ratio < ratio:
            new_w, new_h = width, width / max_ratio

        return int(new_w), int(new_h)

    def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        force_single: bool = False,
        image_urls: Optional[List[str]] = None,
        max_retries: int = 15,
        polling_interval: int = 4
    ) -> Dict[str, Any]:
        """
        Generate images from text prompt.

        Args:
            prompt: Text prompt for image generation
            width: Desired image width
            height: Desired image height
            force_single: Whether to force single image generation
            image_urls: Optional reference image URLs
            max_retries: Maximum number of polling attempts
            polling_interval: Seconds to wait between polling attempts

        Returns:
            dict: Result containing 'image_urls' and 'task_id'

        Raises:
            Exception: If generation fails
        """
        # Fix dimensions
        fixed_width, fixed_height = self.fix_dimension(width, height)

        # Build request parameters
        submit_params = {
            "req_key": "jimeng_t2i_v40",
            "prompt": prompt,
            "width": fixed_width,
            "height": fixed_height,
            "force_single": force_single
        }

        # Add reference images if provided
        if image_urls and len(image_urls) > 0:
            submit_params["image_urls"] = image_urls

        print(f"Submitting generation task with params: {submit_params}")

        try:
            # Submit task
            resp_submit = self.visual_service.cv_sync2async_submit_task(submit_params)

            # Handle bytes response
            if isinstance(resp_submit, bytes):
                resp_submit = json.loads(resp_submit.decode('utf-8'))

            if resp_submit.get("code") != 10000:
                msg = resp_submit.get("message", "Unknown Error")
                raise Exception(f"Submit Failed: {msg} (Code: {resp_submit.get('code')})")

            task_id = resp_submit["data"]["task_id"]
            print(f"Task submitted successfully, task_id: {task_id}")

            # Poll for results
            req_json = {"return_url": True}
            query_params = {
                "req_key": "jimeng_t2i_v40",
                "task_id": task_id,
                "req_json": json.dumps(req_json)
            }

            for attempt in range(max_retries):
                resp_query = self.visual_service.cv_sync2async_get_result(query_params)

                # Handle bytes response
                if isinstance(resp_query, bytes):
                    resp_query = json.loads(resp_query.decode('utf-8'))

                if resp_query.get("code") != 10000:
                    raise Exception(f"Query Failed: {resp_query.get('message')}")

                data = resp_query.get("data", {})
                status = data.get("status")

                print(f"Polling - Status: {status}, Attempt: {attempt + 1}")

                if status == "done":
                    image_urls_result = data.get("image_urls", [])
                    print(f"Generation completed successfully. Images: {len(image_urls_result)}")
                    return {
                        "image_urls": image_urls_result,
                        "task_id": task_id
                    }
                elif status in ["in_queue", "generating"]:
                    time.sleep(polling_interval)
                    continue
                else:
                    raise Exception(f"Unexpected task status: {status}")

            raise Exception("Generation Timeout")

        except Exception as e:
            print(f"Error during image generation: {str(e)}")
            raise e

    def get_available_models(self) -> List[str]:
        """
        Get list of available models. (Currently only jimeng_t2i_v40 is supported)

        Returns:
            list: List of available model names
        """
        return ["jimeng_t2i_v40"]

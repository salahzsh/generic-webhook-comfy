# Package Modules
import os
import json
from typing import Union, Dict, List, Optional, Tuple
import time

# ComfyUI Modules
import folder_paths
from comfy.utils import ProgressBar

# Your Modules
from .modules.webhook_sender import WebhookSender


class WebhookNotificationNode:
    """
    ComfyUI node for sending webhook notifications with images and JSON data
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "webhook_url": ("STRING", {"default": "https://your-webhook-url.com/endpoint", "label": "Webhook URL", "placeholder": "Enter the webhook endpoint URL"}),
                "images": ("IMAGE",),  # ComfyUI image input
            },
            "optional": {
                "json_data": ("STRING", {"default": "{}", "multiline": True, "label": "JSON Data", "placeholder": "Enter JSON data to send with the webhook"}),
                "custom_headers": ("STRING", {"default": "{}", "multiline": True, "label": "Custom Headers", "placeholder": "Enter custom HTTP headers as JSON"}),
                "timeout": ("INT", {"default": 30, "min": 5, "max": 300, "label": "Timeout (seconds)"}),
                "send_as_json": ("BOOLEAN", {"default": False, "label": "Send as JSON Only"}),
                "enable_notification": ("BOOLEAN", {"default": True, "label": "Enable Webhook"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("status", "response")
    FUNCTION = "send_webhook"
    CATEGORY = "Webhook"
    OUTPUT_NODE = True

    def send_webhook(self,
                    webhook_url: str,
                    images: List,
                    json_data: str = "{}",
                    custom_headers: str = "{}",
                    timeout: int = 30,
                    send_as_json: bool = False,
                    enable_notification: bool = True) -> Tuple[str, str]:
        
        if not enable_notification:
            return ("Skipped", "Webhook notification disabled")
        
        # Initialize progress bar
        total_steps = 3
        pbar = ProgressBar(total_steps)
        pbar.update(0)
        
        try:
            # Debug: Check what we received
            print(f"Debug: Received images type: {type(images)}")
            if images is not None:
                print(f"Debug: Images length: {len(images)}")
                if len(images) > 0:
                    print(f"Debug: First image type: {type(images[0])}")
                    if hasattr(images[0], 'shape'):
                        print(f"Debug: First image shape: {images[0].shape}")
            else:
                print("Debug: Images is None")
            
            # Parse JSON data
            try:
                parsed_json = json.loads(json_data) if json_data.strip() else {}
            except json.JSONDecodeError as e:
                return ("Error", f"Invalid JSON data: {str(e)}")
            
            # Parse custom headers
            try:
                parsed_headers = json.loads(custom_headers) if custom_headers.strip() else {}
            except json.JSONDecodeError as e:
                return ("Error", f"Invalid headers JSON: {str(e)}")
            
            pbar.update(1)
            
            # Initialize webhook sender
            webhook_sender = WebhookSender()
            
            pbar.update(2)
            
            # Send webhook
            result = webhook_sender.send_webhook(
                url=webhook_url,
                images=images,
                json_data=parsed_json,
                headers=parsed_headers,
                timeout=timeout,
                send_as_json=send_as_json
            )
            
            pbar.update(3)
            
            # Format response
            if result['success']:
                status = f"Success ({result['status_code']})"
                response = f"Response: {result['response_text']}"
            else:
                status = "Failed"
                response = f"Error: {result.get('error', 'Unknown error')}"
            
            return (status, response)
            
        except Exception as e:
            return ("Error", f"Unexpected error: {str(e)}")


# Node class mapping for ComfyUI
NODE_CLASS_MAPPINGS = {
    "WebhookNotification": WebhookNotificationNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WebhookNotification": "Webhook Notification"
}

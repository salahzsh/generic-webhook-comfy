# Package Modules
import os
import json
from typing import Union, Dict, List, Optional, Tuple, Any
import time

# ComfyUI Modules
import folder_paths
from comfy.utils import ProgressBar

# Your Modules
from .modules.webhook_sender import WebhookSender


class WebhookNotificationNode:
    """
    ComfyUI node for sending webhook notifications with a single image and JSON data
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "webhook_url": ("STRING", {"default": "https://your-webhook-url.com/endpoint", "label": "Webhook URL", "placeholder": "Enter the webhook endpoint URL"}),
                "image": ("IMAGE",),  # ComfyUI image input - single image only
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
                    image: Any,
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
            print(f"Debug: Received image type: {type(image)}")
            if image is not None:
                print(f"Debug: Image shape: {image.shape}")
            else:
                print("Debug: Image is None")
            
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
                image=image, # Pass a list with a single image
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


class GenericWebhookNode:
    """
    Generic ComfyUI node for sending webhook notifications with any input data
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "webhook_url": ("STRING", {"default": "https://your-webhook-url.com/endpoint", "label": "Webhook URL", "placeholder": "Enter the webhook endpoint URL"}),
            },
            "optional": {
                "any_input": (None,),  # Accepts any input type
                "json_data": ("STRING", {"default": "{}", "multiline": True, "label": "Additional JSON Data", "placeholder": "Enter additional JSON data to send with the webhook"}),
                "custom_headers": ("STRING", {"default": "{}", "multiline": True, "label": "Custom Headers", "placeholder": "Enter custom HTTP headers as JSON"}),
                "timeout": ("INT", {"default": 30, "min": 5, "max": 300, "label": "Timeout (seconds)"}),
                "http_method": (["POST", "PUT", "PATCH"], {"default": "POST", "label": "HTTP Method"}),
                "enable_notification": ("BOOLEAN", {"default": True, "label": "Enable Webhook"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("status", "response")
    FUNCTION = "send_generic_webhook"
    CATEGORY = "Webhook"
    OUTPUT_NODE = True

    def send_generic_webhook(self,
                           webhook_url: str,
                           any_input: Any = None,
                           json_data: str = "{}",
                           custom_headers: str = "{}",
                           timeout: int = 30,
                           http_method: str = "POST",
                           enable_notification: bool = True) -> Tuple[str, str]:
        
        if not enable_notification:
            return ("Skipped", "Webhook notification disabled")
        
        # Initialize progress bar
        total_steps = 3
        pbar = ProgressBar(total_steps)
        pbar.update(0)
        
        try:
            # Parse additional JSON data
            try:
                additional_json = json.loads(json_data) if json_data.strip() else {}
            except json.JSONDecodeError as e:
                return ("Error", f"Invalid JSON data: {str(e)}")
            
            # Parse custom headers
            try:
                parsed_headers = json.loads(custom_headers) if custom_headers.strip() else {}
            except json.JSONDecodeError as e:
                return ("Error", f"Invalid headers JSON: {str(e)}")
            
            pbar.update(1)
            
            # Prepare payload data
            payload = self._prepare_payload(any_input, additional_json)
            
            pbar.update(2)
            
            # Send webhook
            result = self._send_request(
                url=webhook_url,
                payload=payload,
                headers=parsed_headers,
                timeout=timeout,
                method=http_method
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
    
    def _prepare_payload(self, any_input: Any, additional_json: Dict) -> Dict:
        """
        Prepare the payload by converting any input to a serializable format
        """
        payload = additional_json.copy()
        
        if any_input is not None:
            # Convert input to a serializable format
            input_data = self._convert_to_serializable(any_input)
            payload['input_data'] = input_data
            payload['input_type'] = str(type(any_input).__name__)
        
        # Add metadata
        payload['timestamp'] = time.time()
        payload['source'] = 'ComfyUI Generic Webhook'
        
        return payload
    
    def _convert_to_serializable(self, obj: Any) -> Any:
        """
        Convert any object to a JSON-serializable format
        """
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (list, tuple)):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {str(k): self._convert_to_serializable(v) for k, v in obj.items()}
        elif hasattr(obj, 'shape'):  # NumPy arrays or tensors
            try:
                # Try to convert to list
                return obj.tolist() if hasattr(obj, 'tolist') else obj.tolist()
            except:
                return str(obj)
        elif hasattr(obj, '__dict__'):
            # Convert objects to dict
            return {k: self._convert_to_serializable(v) for k, v in obj.__dict__.items()}
        else:
            # Fallback to string representation
            return str(obj)
    
    def _send_request(self, url: str, payload: Dict, headers: Dict, timeout: int, method: str) -> Dict:
        """
        Send HTTP request with the prepared payload
        """
        try:
            # Set default headers
            if not headers:
                headers = {
                    'User-Agent': 'ComfyUI-Generic-Webhook/1.0',
                    'Content-Type': 'application/json'
                }
            elif 'Content-Type' not in headers:
                headers['Content-Type'] = 'application/json'
            
            print(f"[GenericWebhook] Sending {method} request:")
            print(f"  URL: {url}")
            print(f"  Headers: {headers}")
            print(f"  Payload: {json.dumps(payload, indent=2)}")
            
            # Send request
            import requests
            session = requests.Session()
            
            if method == "POST":
                response = session.post(url, json=payload, headers=headers, timeout=timeout)
            elif method == "PUT":
                response = session.put(url, json=payload, headers=headers, timeout=timeout)
            elif method == "PATCH":
                response = session.patch(url, json=payload, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            print(f"[GenericWebhook] Response: {response.status_code} {response.text}")
            
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response_text': response.text,
                'headers': dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            print(f"[GenericWebhook] RequestException: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
                'response_text': None,
                'headers': None
            }
        except Exception as e:
            print(f"[GenericWebhook] Unexpected error: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'status_code': None,
                'response_text': None,
                'headers': None
            }


class NotifyServer:
    """
    ComfyUI node for sending simple notifications with a trigger
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "trigger": ("BOOLEAN", {"default": True}),  # Optional trigger
            },
            "optional": {
                "webhook_url": ("STRING", {"default": "https://your-server.com/api/notify", "label": "Webhook URL", "placeholder": "Enter the webhook endpoint URL"}),
                "json_data": ("STRING", {"default": "{}", "multiline": True, "label": "JSON Data", "placeholder": "Enter JSON data to send with the webhook"}),
                "custom_headers": ("STRING", {"default": "{}", "multiline": True, "label": "Custom Headers", "placeholder": "Enter custom HTTP headers as JSON"}),
                "timeout": ("INT", {"default": 30, "min": 5, "max": 300, "label": "Timeout (seconds)"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("output", "status")
    FUNCTION = "notify"
    CATEGORY = "Webhook"
    OUTPUT_NODE = True

    def notify(self, 
               trigger: bool,
               webhook_url: str = "https://your-server.com/api/notify",
               json_data: str = "{}",
               custom_headers: str = "{}",
               timeout: int = 30) -> Tuple[str, str]:
        
        if not trigger:
            print("🔕 NotifyServer: Trigger was False, no notification sent.")
            return ("Skipped", "Trigger was False, no notification sent.")
        
        try:
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
            
            # Set default headers
            if not parsed_headers:
                parsed_headers = {
                    'User-Agent': 'ComfyUI-NotifyServer/1.0',
                    'Content-Type': 'application/json'
                }
            elif 'Content-Type' not in parsed_headers:
                parsed_headers['Content-Type'] = 'application/json'
            
            # Prepare payload
            payload = parsed_json.copy()
            payload['status'] = 'triggered'
            payload['timestamp'] = time.time()
            payload['source'] = 'ComfyUI NotifyServer'
            
            print(f"[NotifyServer] Sending notification:")
            print(f"  URL: {webhook_url}")
            print(f"  Headers: {parsed_headers}")
            print(f"  Payload: {json.dumps(payload, indent=2)}")
            
            # Send request
            import requests
            response = requests.post(webhook_url, json=payload, headers=parsed_headers, timeout=timeout)
            
            print(f"[NotifyServer] Response: {response.status_code} {response.text}")
            
            if response.status_code < 400:
                print("✅ NotifyServer: Notification sent successfully.")
                return ("Success", f"Notification sent successfully ({response.status_code})")
            else:
                print(f"❌ NotifyServer: Failed to notify server - {response.status_code}")
                return ("Failed", f"Failed to notify server - {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ NotifyServer: Request failed - {e}")
            return ("Error", f"Request failed: {str(e)}")
        except Exception as e:
            print(f"❌ NotifyServer: Unexpected error - {e}")
            return ("Error", f"Unexpected error: {str(e)}")


class DelayNode:
    """
    ComfyUI node for adding delays/sleep in workflows
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "delay_seconds": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3600.0, "step": 0.1, "label": "Delay (seconds)"}),
            },
            "optional": {
                "show_progress": ("BOOLEAN", {"default": True, "label": "Show Progress Bar"}),
                "enable_delay": ("BOOLEAN", {"default": True, "label": "Enable Delay"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("output", "status")
    FUNCTION = "delay"
    CATEGORY = "Utility"

    def delay(self,
              delay_seconds: float,
              show_progress: bool = True,
              enable_delay: bool = True,
              **kwargs) -> Tuple[str, str]:
        
        if not enable_delay:
            return ("Delay disabled", "Delay disabled")
        
        try:
            # Validate delay time
            if delay_seconds < 0:
                return ("Error: Delay time cannot be negative", "Error: Delay time cannot be negative")
            
            if delay_seconds == 0:
                return ("No delay", "No delay (0 seconds)")
            
            print(f"[DelayNode] Starting delay of {delay_seconds} seconds...")
            
            if show_progress:
                # Create progress bar for visual feedback
                total_steps = int(delay_seconds * 10)  # Update every 0.1 seconds
                if total_steps < 1:
                    total_steps = 1
                
                pbar = ProgressBar(total_steps)
                
                # Sleep in small increments to show progress
                remaining_time = delay_seconds
                step_time = 0.1
                
                for i in range(total_steps):
                    if remaining_time <= step_time:
                        time.sleep(remaining_time)
                        pbar.update(total_steps)
                        break
                    else:
                        time.sleep(step_time)
                        remaining_time -= step_time
                        pbar.update(i + 1)
            else:
                # Simple sleep without progress bar
                time.sleep(delay_seconds)
            
            print(f"[DelayNode] Delay completed ({delay_seconds} seconds)")
            return ("Delay completed", f"Delay completed ({delay_seconds} seconds)")
            
        except Exception as e:
            print(f"[DelayNode] Error during delay: {str(e)}")
            return (f"Error: {str(e)}", f"Error: {str(e)}")


class DelayImageNode:
    """
    ComfyUI node for adding delays/sleep in workflows with image support
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "delay_seconds": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3600.0, "step": 0.1, "label": "Delay (seconds)"}),
                "image": ("IMAGE",),  # ComfyUI image input
            },
            "optional": {
                "show_progress": ("BOOLEAN", {"default": True, "label": "Show Progress Bar"}),
                "enable_delay": ("BOOLEAN", {"default": True, "label": "Enable Delay"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "status")
    FUNCTION = "delay_image"
    CATEGORY = "Utility"

    def delay_image(self,
                   delay_seconds: float,
                   image: Any,
                   show_progress: bool = True,
                   enable_delay: bool = True) -> Tuple[Any, str]:
        
        if not enable_delay:
            return (image, "Delay disabled")
        
        try:
            # Validate delay time
            if delay_seconds < 0:
                return (image, "Error: Delay time cannot be negative")
            
            if delay_seconds == 0:
                return (image, "No delay (0 seconds)")
            
            print(f"[DelayImageNode] Starting delay of {delay_seconds} seconds...")
            
            if show_progress:
                # Create progress bar for visual feedback
                total_steps = int(delay_seconds * 10)  # Update every 0.1 seconds
                if total_steps < 1:
                    total_steps = 1
                
                pbar = ProgressBar(total_steps)
                
                # Sleep in small increments to show progress
                remaining_time = delay_seconds
                step_time = 0.1
                
                for i in range(total_steps):
                    if remaining_time <= step_time:
                        time.sleep(remaining_time)
                        pbar.update(total_steps)
                        break
                    else:
                        time.sleep(step_time)
                        remaining_time -= step_time
                        pbar.update(i + 1)
            else:
                # Simple sleep without progress bar
                time.sleep(delay_seconds)
            
            print(f"[DelayImageNode] Delay completed ({delay_seconds} seconds)")
            return (image, f"Delay completed ({delay_seconds} seconds)")
            
        except Exception as e:
            print(f"[DelayImageNode] Error during delay: {str(e)}")
            return (image, f"Error: {str(e)}")


class DelayLatentNode:
    """
    ComfyUI node for adding delays/sleep in workflows with latent support
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "delay_seconds": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3600.0, "step": 0.1, "label": "Delay (seconds)"}),
                "latent": ("LATENT",),  # ComfyUI latent input
            },
            "optional": {
                "show_progress": ("BOOLEAN", {"default": True, "label": "Show Progress Bar"}),
                "enable_delay": ("BOOLEAN", {"default": True, "label": "Enable Delay"}),
            }
        }

    RETURN_TYPES = ("LATENT", "STRING")
    RETURN_NAMES = ("latent", "status")
    FUNCTION = "delay_latent"
    CATEGORY = "Utility"

    def delay_latent(self,
                    delay_seconds: float,
                    latent: Any,
                    show_progress: bool = True,
                    enable_delay: bool = True) -> Tuple[Any, str]:
        
        if not enable_delay:
            return (latent, "Delay disabled")
        
        try:
            # Validate delay time
            if delay_seconds < 0:
                return (latent, "Error: Delay time cannot be negative")
            
            if delay_seconds == 0:
                return (latent, "No delay (0 seconds)")
            
            print(f"[DelayLatentNode] Starting delay of {delay_seconds} seconds...")
            
            if show_progress:
                # Create progress bar for visual feedback
                total_steps = int(delay_seconds * 10)  # Update every 0.1 seconds
                if total_steps < 1:
                    total_steps = 1
                
                pbar = ProgressBar(total_steps)
                
                # Sleep in small increments to show progress
                remaining_time = delay_seconds
                step_time = 0.1
                
                for i in range(total_steps):
                    if remaining_time <= step_time:
                        time.sleep(remaining_time)
                        pbar.update(total_steps)
                        break
                    else:
                        time.sleep(step_time)
                        remaining_time -= step_time
                        pbar.update(i + 1)
            else:
                # Simple sleep without progress bar
                time.sleep(delay_seconds)
            
            print(f"[DelayLatentNode] Delay completed ({delay_seconds} seconds)")
            return (latent, f"Delay completed ({delay_seconds} seconds)")
            
        except Exception as e:
            print(f"[DelayLatentNode] Error during delay: {str(e)}")
            return (latent, f"Error: {str(e)}")


class DelayConditioningNode:
    """
    ComfyUI node for adding delays/sleep in workflows with conditioning support
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "delay_seconds": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 3600.0, "step": 0.1, "label": "Delay (seconds)"}),
                "conditioning": ("CONDITIONING",),  # ComfyUI conditioning input
            },
            "optional": {
                "show_progress": ("BOOLEAN", {"default": True, "label": "Show Progress Bar"}),
                "enable_delay": ("BOOLEAN", {"default": True, "label": "Enable Delay"}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "STRING")
    RETURN_NAMES = ("conditioning", "status")
    FUNCTION = "delay_conditioning"
    CATEGORY = "Utility"

    def delay_conditioning(self,
                          delay_seconds: float,
                          conditioning: Any,
                          show_progress: bool = True,
                          enable_delay: bool = True) -> Tuple[Any, str]:
        
        if not enable_delay:
            return (conditioning, "Delay disabled")
        
        try:
            # Validate delay time
            if delay_seconds < 0:
                return (conditioning, "Error: Delay time cannot be negative")
            
            if delay_seconds == 0:
                return (conditioning, "No delay (0 seconds)")
            
            print(f"[DelayConditioningNode] Starting delay of {delay_seconds} seconds...")
            
            if show_progress:
                # Create progress bar for visual feedback
                total_steps = int(delay_seconds * 10)  # Update every 0.1 seconds
                if total_steps < 1:
                    total_steps = 1
                
                pbar = ProgressBar(total_steps)
                
                # Sleep in small increments to show progress
                remaining_time = delay_seconds
                step_time = 0.1
                
                for i in range(total_steps):
                    if remaining_time <= step_time:
                        time.sleep(remaining_time)
                        pbar.update(total_steps)
                        break
                    else:
                        time.sleep(step_time)
                        remaining_time -= step_time
                        pbar.update(i + 1)
            else:
                # Simple sleep without progress bar
                time.sleep(delay_seconds)
            
            print(f"[DelayConditioningNode] Delay completed ({delay_seconds} seconds)")
            return (conditioning, f"Delay completed ({delay_seconds} seconds)")
            
        except Exception as e:
            print(f"[DelayConditioningNode] Error during delay: {str(e)}")
            return (conditioning, f"Error: {str(e)}")


class TriggerNode:
    """
    ComfyUI node that accepts any input and outputs a boolean trigger
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "any_input": (None,),  # Accepts any input type
            },
            "optional": {
                "always_trigger": ("BOOLEAN", {"default": True, "label": "Always Trigger"}),
            }
        }

    RETURN_TYPES = ("BOOLEAN", "STRING")
    RETURN_NAMES = ("trigger", "status")
    FUNCTION = "trigger"
    CATEGORY = "Utility"

    def trigger(self, any_input: Any, always_trigger: bool = True) -> Tuple[bool, str]:
        """
        Convert any input to a boolean trigger
        """
        try:
            # Always return True if always_trigger is True
            if always_trigger:
                return (True, f"Triggered by {type(any_input).__name__}")
            
            # Otherwise, check if input has meaningful content
            if any_input is None:
                return (False, "No input provided")
            elif isinstance(any_input, (list, tuple)) and len(any_input) == 0:
                return (False, "Empty list/tuple input")
            elif isinstance(any_input, dict) and len(any_input) == 0:
                return (False, "Empty dict input")
            elif isinstance(any_input, str) and not any_input.strip():
                return (False, "Empty string input")
            else:
                return (True, f"Triggered by {type(any_input).__name__}")
                
        except Exception as e:
            return (False, f"Error processing input: {str(e)}")


# Node class mapping for ComfyUI
NODE_CLASS_MAPPINGS = {
    "WebhookNotification": WebhookNotificationNode,
    "GenericWebhook": GenericWebhookNode,
    "NotifyServer": NotifyServer,
    "Trigger": TriggerNode,
    "Delay": DelayNode,
    "DelayImage": DelayImageNode,
    "DelayLatent": DelayLatentNode,
    "DelayConditioning": DelayConditioningNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WebhookNotification": "Webhook Notification",
    "GenericWebhook": "Generic Webhook",
    "NotifyServer": "Notify Server",
    "Trigger": "Trigger",
    "Delay": "Delay/Sleep",
    "DelayImage": "Delay/Sleep (Image)",
    "DelayLatent": "Delay/Sleep (Latent)",
    "DelayConditioning": "Delay/Sleep (Conditioning)"
}

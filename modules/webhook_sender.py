import requests
import json
import base64
from typing import Dict, List, Optional, Union, Any
from PIL import Image
import io
import numpy as np


def convert_tensor_to_pil(tensor):
    """
    Convert ComfyUI image tensor to PIL Image
    
    Args:
        tensor: ComfyUI image tensor (numpy array or torch tensor)
        
    Returns:
        PIL Image object
    """
    if tensor is None:
        return None
    
    # Ensure tensor is numpy array
    if hasattr(tensor, 'cpu'):
        tensor = tensor.cpu().numpy()
    elif not isinstance(tensor, np.ndarray):
        tensor = np.array(tensor)
    
    # Handle different tensor formats
    if len(tensor.shape) == 4:  # Batch dimension
        tensor = tensor[0]  # Take first image from batch
    elif len(tensor.shape) == 3:
        pass  # Already in correct format
    else:
        raise ValueError(f"Unexpected tensor shape: {tensor.shape}")
    
    # Convert from [0, 1] to [0, 255] range
    if tensor.max() <= 1.0:
        tensor = (tensor * 255).astype(np.uint8)
    else:
        tensor = tensor.astype(np.uint8)
    
    # Convert to PIL Image
    return Image.fromarray(tensor)


class WebhookSender:
    def __init__(self):
        self.session = requests.Session()
    
    def send_webhook(self, 
                    url: str, 
                    image: Any, 
                    json_data: Optional[Dict] = {},
                    headers: Optional[Dict] = None,
                    timeout: int = 30,
                    send_as_json: bool = False) -> Dict:
        """
        Send a webhook POST request with image and JSON data
        
        Args:
            url: The webhook URL to send the request to
            image: ComfyUI image tensor to send
            json_data: Optional JSON data to include in the request
            headers: Optional custom headers
            timeout: Request timeout in seconds
            send_as_json: If True, send only JSON data (no images)
            
        Returns:
            Dict containing response status and data
        """
        try:
            # Set default headers if none provided
            if headers is None:
                headers = {
                    'User-Agent': 'ComfyUI-Webhook/1.0'
                }
            
            if send_as_json:
                # Send as pure JSON request
                
                headers['Content-Type'] = 'application/json'
                print("[WebhookSender] Sending JSON request:")
                print(f"  URL: {url}")
                print(f"  Headers: {headers}")
                print(f"  JSON Payload: {json.dumps(json_data, indent=2)}")
                
                response = self.session.post(
                    url,
                    json=json_data,
                    headers=headers,
                    timeout=timeout
                )
                print(f"[WebhookSender] Response: {response.status_code} {response.text}")
            else:
                # Prepare the multipart form data
                files = []
                data = {}
                
                # Convert and add image to files
                if image is not None:
                    print("[WebhookSender] Preparing to send image as multipart form data.")
                    try:
                        pil_image = convert_tensor_to_pil(image)
                        if pil_image is not None:
                            img_buffer = io.BytesIO()
                            pil_image.save(img_buffer, format='PNG')
                            img_buffer.seek(0)
                            files.append(('image', ('image.png', img_buffer, 'image/png')))
                            print(f"  Added image.png to files (size: {img_buffer.getbuffer().nbytes} bytes)")
                    except Exception as e:
                        print(f"Warning: Failed to convert image: {str(e)}")
                else:
                    print("[WebhookSender] No image to send.")
                
                if json_data:
                    data['payload'] = json.dumps(json_data)
                    print(f"  JSON data field: {data['payload']}")
                print(f"[WebhookSender] Sending multipart request:")
                print(f"  URL: {url}")
                print(f"  Headers: {headers}")
                print(f"  Data fields: {list(data.keys())}")
                print(f"  Files: {[f[1][0] for f in files]}")
                
                response = self.session.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=timeout
                )
                print(f"[WebhookSender] Response: {response.status_code} {response.text}")
            
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response_text': response.text,
                'headers': dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            print(f"[WebhookSender] RequestException: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'status_code': None,
                'response_text': None,
                'headers': None
            }
        except Exception as e:
            print(f"[WebhookSender] Unexpected error: {str(e)}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'status_code': None,
                'response_text': None,
                'headers': None
            } 
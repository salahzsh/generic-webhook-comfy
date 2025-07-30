# Generic Webhook Node Usage Guide

The **Generic Webhook** node is a flexible ComfyUI node that can accept any input type and automatically convert it to a JSON-serializable format for webhook notifications.

## Key Features

- **Universal Input Support**: Accepts any ComfyUI output type (images, text, numbers, objects, etc.)
- **Automatic Conversion**: Converts any input to JSON-serializable format
- **Multiple HTTP Methods**: Supports POST, PUT, and PATCH requests
- **Custom Headers**: Add authentication tokens or custom headers
- **Progress Tracking**: Visual progress bar during request execution
- **Error Handling**: Detailed error messages and response feedback

## Basic Usage

### 1. Simple Text Notification

Connect a text output to notify your server when text processing completes:

```json
{
  "input_data": "processed_text_content",
  "input_type": "str",
  "timestamp": 1234567890.123,
  "source": "ComfyUI Generic Webhook",
  "message": "Text processing completed"
}
```

### 2. Image Generation Notification

Connect an image output to notify when image generation finishes:

```json
{
  "input_data": [[[[0.5, 0.3, 0.8], ...]]],
  "input_type": "ndarray",
  "timestamp": 1234567890.123,
  "source": "ComfyUI Generic Webhook",
  "workflow_name": "Image Generation"
}
```

### 3. Parameter Tracking

Connect model parameters to track generation settings:

```json
{
  "input_data": {
    "steps": 20,
    "cfg": 7.5,
    "seed": 12345,
    "sampler": "euler"
  },
  "input_type": "dict",
  "timestamp": 1234567890.123,
  "source": "ComfyUI Generic Webhook"
}
```

## Input Type Handling

The node automatically handles different input types:

### Primitive Types
- **Strings**: Sent as-is
- **Numbers**: Sent as-is
- **Booleans**: Sent as-is
- **None**: Sent as null

### Complex Types
- **Lists/Tuples**: Converted to arrays
- **Dictionaries**: Converted to objects
- **NumPy Arrays**: Converted to nested arrays
- **Tensors**: Converted to nested arrays
- **Objects**: Converted to dictionaries (using `__dict__`)
- **Other**: Converted to string representation

## Node Parameters

### Required
- **webhook_url**: The endpoint URL to send the webhook to

### Optional
- **any_input**: Connect any ComfyUI output here
- **json_data**: Additional JSON data to merge into the payload
- **custom_headers**: HTTP headers (e.g., for authentication)
- **timeout**: Request timeout in seconds (5-300)
- **http_method**: POST, PUT, or PATCH
- **enable_notification**: Toggle to enable/disable the webhook

## Example Workflows

### 1. Image Generation with Multiple Notifications

```json
{
  "nodes": [
    {
      "id": 1,
      "type": "KSampler",
      "title": "Image Generator"
    },
    {
      "id": 2,
      "type": "GenericWebhook",
      "title": "Generation Start",
      "widgets_values": [
        "https://your-server.com/generation-start",
        "{\"status\": \"started\"}",
        "{\"Authorization\": \"Bearer token\"}",
        30,
        "POST",
        true
      ]
    },
    {
      "id": 3,
      "type": "GenericWebhook",
      "title": "Generation Complete",
      "widgets_values": [
        "https://your-server.com/generation-complete",
        "{\"status\": \"completed\"}",
        "{}",
        30,
        "POST",
        true
      ]
    }
  ],
  "links": [
    [1, 1, 0, 2, 1],  // Connect sampler output to start notification
    [2, 1, 0, 3, 1]   // Connect sampler output to complete notification
  ]
}
```

### 2. Text Processing Pipeline

```json
{
  "nodes": [
    {
      "id": 1,
      "type": "CLIPTextEncode",
      "title": "Text Encoder"
    },
    {
      "id": 2,
      "type": "GenericWebhook",
      "title": "Text Processed",
      "widgets_values": [
        "https://your-server.com/text-processed",
        "{\"action\": \"text_encoded\"}",
        "{}",
        30,
        "POST",
        true
      ]
    }
  ],
  "links": [
    [1, 1, 0, 2, 1]  // Connect encoded text to webhook
  ]
}
```

## Server-Side Handling

### Express.js Example

```javascript
app.post('/webhook', (req, res) => {
  const { input_data, input_type, timestamp, source, ...additionalData } = req.body;
  
  console.log('Received webhook:', {
    inputType: input_type,
    inputData: input_data,
    timestamp: new Date(timestamp * 1000),
    additionalData
  });
  
  // Process based on input type
  switch (input_type) {
    case 'str':
      handleTextData(input_data);
      break;
    case 'ndarray':
      handleImageData(input_data);
      break;
    case 'dict':
      handleParameterData(input_data);
      break;
    default:
      handleGenericData(input_data);
  }
  
  res.json({ success: true, received: true });
});
```

### Python Flask Example

```python
from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    data = request.json
    
    input_data = data.get('input_data')
    input_type = data.get('input_type')
    timestamp = data.get('timestamp')
    source = data.get('source')
    
    print(f"Received {input_type} data at {datetime.fromtimestamp(timestamp)}")
    print(f"Input data: {input_data}")
    
    # Process based on input type
    if input_type == 'str':
        process_text(input_data)
    elif input_type == 'ndarray':
        process_image_array(input_data)
    elif input_type == 'dict':
        process_parameters(input_data)
    
    return jsonify({'success': True, 'processed': True})

def process_text(text):
    print(f"Processing text: {text}")
    # Your text processing logic here

def process_image_array(image_array):
    print(f"Processing image array with shape: {len(image_array)}")
    # Your image processing logic here

def process_parameters(params):
    print(f"Processing parameters: {params}")
    # Your parameter processing logic here

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## Best Practices

### 1. Use Descriptive JSON Data
```json
{
  "workflow_name": "Portrait Generation",
  "user_id": "user123",
  "priority": "high",
  "expected_duration": 30
}
```

### 2. Add Authentication Headers
```json
{
  "Authorization": "Bearer your-secret-token",
  "X-API-Key": "your-api-key",
  "Content-Type": "application/json"
}
```

### 3. Handle Different HTTP Methods
- **POST**: For creating new resources
- **PUT**: For updating existing resources
- **PATCH**: For partial updates

### 4. Set Appropriate Timeouts
- Short operations: 10-30 seconds
- Long operations: 60-300 seconds
- Consider your server's processing time

### 5. Error Handling
Always check the webhook response:
- Success: Status code < 400
- Failure: Check error message in response

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Increase timeout value
   - Check server availability
   - Verify URL is correct

2. **Invalid JSON**
   - Check JSON syntax in additional data
   - Ensure custom headers are valid JSON

3. **Authentication Errors**
   - Verify API keys/tokens
   - Check header format
   - Ensure server accepts your authentication method

4. **Large Payloads**
   - Consider compressing data
   - Split large operations into smaller chunks
   - Use streaming for very large data

### Debug Mode

Enable debug logging by checking the ComfyUI console for detailed information about:
- Request payload
- Response status
- Error messages
- Processing steps
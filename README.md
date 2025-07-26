# ComfyUI Webhook Notification Node

A custom ComfyUI node that allows you to send webhook notifications with images and JSON data to external servers.

## Features

- Send POST requests to webhook URLs
- Include one or more images in the request
- Send custom JSON data payload
- Custom HTTP headers support
- Configurable timeout settings
- Progress bar for request status
- Error handling and response feedback

## Installation

1. Clone or download this repository to your ComfyUI `custom_nodes` directory
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Restart ComfyUI

## Usage

### Basic Usage

1. Add the "Webhook Notification" node to your workflow
2. Connect an image output to the "images" input
3. Set your webhook URL in the "webhook_url" field
4. Optionally add JSON data in the "json_data" field
5. Run your workflow

### Node Parameters

#### Required Parameters
- **webhook_url**: The URL where the webhook will be sent
- **images**: Image input from other nodes

#### Optional Parameters
- **json_data**: JSON string to include in the request (default: `{}`)
- **custom_headers**: JSON string for custom HTTP headers (default: `{}`)
- **timeout**: Request timeout in seconds (default: 30, range: 5-300)
- **send_as_json**: If enabled, sends only JSON data without images (default: false)
- **enable_notification**: Toggle to enable/disable webhook sending (default: true)

### Outputs
- **status**: Success/failure status of the webhook request
- **response**: Response text or error message from the server

## Example JSON Data

```json
{
  "workflow_name": "My Image Generation",
  "timestamp": "2024-01-01T12:00:00Z",
  "parameters": {
    "prompt": "A beautiful landscape",
    "seed": 12345
  }
}
```

## Example Custom Headers

```json
{
  "Authorization": "Bearer your-token-here",
  "X-Custom-Header": "custom-value"
}
```

## Request Formats

### Multipart Form Data (Default)
When `send_as_json` is disabled (default), the webhook sends a multipart form request with:
- Images as files with names `image_0.png`, `image_1.png`, etc.
- JSON data in the `json_data` field

### JSON Only
When `send_as_json` is enabled, the webhook sends a pure JSON request with:
- Content-Type: `application/json`
- JSON data as the request body

## Error Handling

The node provides detailed error messages for:
- Invalid JSON data
- Network connection issues
- Server errors
- Timeout errors

## Next.js Handler Example

For your Next.js application, use this handler that supports both JSON-only and multipart requests:

```typescript
import { NextRequest, NextResponse } from "next/server"

interface WebhookRequestBody {
    characterId: string
    workflow_name?: string
    prompt?: string
    seed?: number
    timestamp?: string
    [key: string]: any
}

export async function POST(request: NextRequest) {
    try {
        const contentType = request.headers.get('content-type') || ''
        
        if (contentType.includes('application/json')) {
            // Handle JSON-only requests
            const body: WebhookRequestBody = await request.json()
            
            if (!body.characterId) {
                return NextResponse.json(
                    { error: 'characterId is required' },
                    { status: 400 }
                )
            }
            
            console.log('Received JSON webhook:', body)
            
            return NextResponse.json({ 
                success: true, 
                characterId: body.characterId 
            }, { status: 201 })
        } else if (contentType.includes('multipart/form-data')) {
            // Handle multipart form data (images + JSON)
            const formData = await request.formData()
            const jsonDataStr = formData.get('json_data') as string
            const images = formData.getAll('images') as File[]
            
            const jsonData: WebhookRequestBody = JSON.parse(jsonDataStr)
            
            if (!jsonData.characterId) {
                return NextResponse.json(
                    { error: 'characterId is required in JSON data' },
                    { status: 400 }
                )
            }
            
            console.log('Received multipart webhook:', {
                characterId: jsonData.characterId,
                imageCount: images.length
            })
            
            return NextResponse.json({ 
                success: true, 
                characterId: jsonData.characterId,
                imagesProcessed: images.length
            }, { status: 201 })
        }
    } catch (error) {
        console.error('Webhook processing error:', error)
        return NextResponse.json(
            { success: false, error: 'Failed to process webhook' },
            { status: 500 }
        )
    }
}
```

## License

This project is open source and available under the MIT License.



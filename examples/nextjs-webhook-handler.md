# NextJS webhook handler example

```typescript
import { NextRequest, NextResponse } from "next/server"
import { createClient } from "@/lib/supabase/server"
import { getCharacter } from "@/lib/supabase/db/character"

// Interface for JSON-only requests
interface WebhookRequestBody {
    characterId: string
}

// Interface for multipart form data
interface MultipartWebhookData {
    json_data: WebhookRequestBody
    images?: File[]
}

export async function POST(request: NextRequest) {
    try {
        const contentType = request.headers.get('content-type') || ''
    
        if (contentType.includes('application/json')) {
            // Handle JSON-only requests (no images only json data)
            return await handleJsonRequest(request)
        } else if (contentType.includes('multipart/form-data')) {
            // Handle multipart form data (images + JSON)
            return await handleMultipartRequest(request)
        } else {
            console.log('Unsupported content type:', contentType)
            return NextResponse.json(
                { error: 'Unsupported content type. Use application/json or multipart/form-data' },
                { status: 400 }
            )
        }
    } catch (error) {
        console.error('Webhook processing error:', error)
        return NextResponse.json(
            { success: false, error: 'Failed to process webhook' },
            { status: 500 }
        )
    }
}

async function handleJsonRequest(request: NextRequest) {
    try {
        const body: WebhookRequestBody = await request.json()

        if (!body.characterId) {
            console.log('Missing characterId in request body')
            return NextResponse.json(
                { error: 'characterId is required' },
                { status: 400 }
            )
        }

        return NextResponse.json({ 
            success: true, 
            message: 'JSON webhook processed successfully',
            characterId: body.characterId 
        }, { status: 201 })
    } catch (error) {
        console.error('JSON request processing error:', error)
        return NextResponse.json(
            { success: false, error: 'Invalid JSON data' },
            { status: 400 }
        )
    }
}

async function handleMultipartRequest(request: NextRequest) {
    try {
        const formData = await request.formData()
        const jsonDataStr = formData.get('payload') as string
        const images = formData.getAll('images') as File[]

        // Parse JSON data
        let jsonData: WebhookRequestBody | null = null
        if (jsonDataStr) {
            try {
                jsonData = JSON.parse(jsonDataStr)
            } catch (e) {
                console.error('Failed to parse JSON data:', e)
                return NextResponse.json(
                    { error: 'Invalid JSON data in form' },
                    { status: 400 }
                )
            }
        }

        if (!jsonData || !jsonData.characterId) {
            return NextResponse.json(
                { error: 'characterId is required in JSON data' },
                { status: 400 }
            )
        }

        // Process images
        const imageInfo = []
        for (let i = 0; i < images.length; i++) {
            const image = images[i]
            if (image) {
                try {
                    // Save image to Supabase storage
                    const imageUrl = await saveImage(image, jsonData.characterId)
                    
                    imageInfo.push({
                        index: i,
                        filename: image.name,
                        size: image.size,
                        type: image.type,
                        url: imageUrl
                    })
                } catch (error) {
                    console.error(`Failed to save image ${i}:`, error)
                    imageInfo.push({
                        index: i,
                        filename: image.name,
                        size: image.size,
                        type: image.type,
                        error: error instanceof Error ? error.message : 'Unknown error'
                    })
                }
            }
        }

        return NextResponse.json({ 
            success: true, 
            message: 'Multipart webhook processed successfully',
            characterId: jsonData.characterId,
            imagesProcessed: imageInfo.length,
            images: imageInfo
        }, { status: 201 })
    } catch (error) {
        console.error('Multipart request processing error:', error)
        return NextResponse.json(
            { success: false, error: 'Failed to process multipart data' },
            { status: 400 }
        )
    }
}

// Helper function to save images to Supabase storage
async function saveImage(image: File, characterId: string): Promise<string> {
    try {                
        // Generate a unique filename with timestamp
        const timestamp = Date.now()
        const fileExtension = image.name.split('.').pop() || 'png'
        const filename = `${characterId}.${fileExtension}`
        const fullPath = `${storagePath}${filename}`
        
        // Convert File to ArrayBuffer
        const bytes = await image.arrayBuffer()
        const buffer = Buffer.from(bytes)

        // Store image somewhere
        
        return true
        
    } catch (error) {
        console.error('Error in saveImage function:', error)
        throw error
    }
} 
```
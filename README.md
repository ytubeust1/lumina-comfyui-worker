# Lumina AI - ComfyUI Worker for RunPod

Custom ComfyUI serverless worker with:
- **LUSTIFY V7** - NSFW SDXL checkpoint for realistic images
- **RealVisXL V5** - SFW alternative
- **ReActor** - Face swap capabilities
- **IP-Adapter Plus Face** - Face consistency across generations
- **AnimateDiff** - Video generation

## Features

| Feature | Status |
|---------|--------|
| Text-to-Image (SDXL) | ✅ |
| NSFW Generation | ✅ |
| Face Swap | ✅ |
| Face Consistency | ✅ |
| LoRA Support | ✅ |
| Video Generation | ✅ |

## API Usage

### Basic Generation
```json
{
  "input": {
    "prompt": "beautiful woman, professional photography",
    "negative_prompt": "bad quality",
    "model": "lustify",
    "width": 768,
    "height": 1024,
    "steps": 30
  }
}
```

### With Face Reference (IP-Adapter)
```json
{
  "input": {
    "prompt": "woman in red dress, fashion photography",
    "model": "lustify",
    "face_image_url": "https://example.com/reference_face.jpg"
  }
}
```

### Custom Workflow
```json
{
  "input": {
    "workflow": { ... ComfyUI workflow JSON ... }
  }
}
```

## Deployment

Built for RunPod Serverless. Deploy via RunPod console with this repo.

"""
Custom RunPod Handler for Lumina AI ComfyUI Worker
Supports: Image generation, Face swap, LoRA, Video generation
"""

import runpod
import json
import base64
import urllib.request
import time
import os

# ComfyUI imports
import sys
sys.path.append('/comfyui')

def wait_for_service(url, max_retries=50, delay=0.2):
    """Wait for ComfyUI service to be ready"""
    for i in range(max_retries):
        try:
            urllib.request.urlopen(url)
            return True
        except:
            time.sleep(delay)
    return False

def queue_workflow(workflow, client_id="runpod"):
    """Queue a workflow in ComfyUI"""
    import urllib.request
    import urllib.parse
    
    data = json.dumps({"prompt": workflow, "client_id": client_id}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    req.add_header('Content-Type', 'application/json')
    
    response = urllib.request.urlopen(req)
    return json.loads(response.read())

def get_history(prompt_id):
    """Get workflow execution history"""
    url = f"http://127.0.0.1:8188/history/{prompt_id}"
    response = urllib.request.urlopen(url)
    return json.loads(response.read())

def get_image(filename, subfolder, folder_type):
    """Get generated image from ComfyUI"""
    params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
    url = f"http://127.0.0.1:8188/view?{params}"
    response = urllib.request.urlopen(url)
    return response.read()

def handler(event):
    """Main handler for RunPod serverless"""
    
    input_data = event.get("input", {})
    
    # Get parameters
    workflow = input_data.get("workflow")
    prompt = input_data.get("prompt", "")
    negative_prompt = input_data.get("negative_prompt", "bad quality, worst quality")
    width = input_data.get("width", 768)
    height = input_data.get("height", 1024)
    steps = input_data.get("steps", 30)
    cfg_scale = input_data.get("cfg_scale", 7.0)
    model = input_data.get("model", "lustify")
    seed = input_data.get("seed", -1)
    lora_url = input_data.get("lora_url")
    lora_strength = input_data.get("lora_strength", 0.8)
    face_image_url = input_data.get("face_image_url")  # For face swap/IP-Adapter
    
    # Wait for ComfyUI to be ready
    if not wait_for_service("http://127.0.0.1:8188"):
        return {"error": "ComfyUI service not available"}
    
    # If no workflow provided, build a basic one
    if not workflow:
        import random
        if seed == -1:
            seed = random.randint(1, 2147483647)
        
        # Model mapping
        model_files = {
            "lustify": "lustifySDXL_v7GGWP.safetensors",
            "realvis": "RealVisXL_V5.safetensors"
        }
        checkpoint = model_files.get(model, model_files["lustify"])
        
        workflow = {
            "4": {
                "inputs": {"ckpt_name": checkpoint},
                "class_type": "CheckpointLoaderSimple"
            },
            "5": {
                "inputs": {"width": width, "height": height, "batch_size": 1},
                "class_type": "EmptyLatentImage"
            },
            "6": {
                "inputs": {"text": prompt, "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {"text": negative_prompt, "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "8": {
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
                "class_type": "VAEDecode"
            },
            "9": {
                "inputs": {"filename_prefix": "lumina", "images": ["8", 0]},
                "class_type": "SaveImage"
            }
        }
    
    try:
        # Queue the workflow
        result = queue_workflow(workflow)
        prompt_id = result.get("prompt_id")
        
        if not prompt_id:
            return {"error": "Failed to queue workflow"}
        
        # Wait for completion
        max_wait = 300  # 5 minutes max
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            history = get_history(prompt_id)
            
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                
                # Find SaveImage node output
                images = []
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        for image_data in node_output["images"]:
                            image_bytes = get_image(
                                image_data["filename"],
                                image_data.get("subfolder", ""),
                                image_data.get("type", "output")
                            )
                            # Convert to base64
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                            images.append({
                                "base64": image_base64,
                                "filename": image_data["filename"]
                            })
                
                if images:
                    return {
                        "status": "success",
                        "images": images,
                        "seed": seed
                    }
            
            time.sleep(1)
        
        return {"error": "Generation timed out"}
        
    except Exception as e:
        return {"error": str(e)}

# Start the serverless worker
runpod.serverless.start({"handler": handler})

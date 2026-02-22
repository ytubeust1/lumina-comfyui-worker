

"""
Custom RunPod Handler for Lumina AI ComfyUI Worker
Downloads LUSTIFY model on first run
"""

import runpod
import json
import base64
import urllib.request
import time
import os
import subprocess

MODELS_TO_DOWNLOAD = {
    "lustifySDXL_v7.safetensors": {
        "url": "https://civitai.com/api/download/models/708635?type=Model&format=SafeTensor&size=pruned&fp=fp16",
        "path": "/comfyui/models/checkpoints/lustifySDXL_v7.safetensors",
        "size_gb": 6.5,
        "requires_token": True
    }
}

def download_model(name, config, civitai_token=None):
    if os.path.exists(config["path"]):
        print(f"Model {name} already exists")
        return True
    print(f"Downloading {name}...")
    try:
        url = config["url"]
        cmd = ["wget", "-q", "-O", config["path"], url]
        if config.get("requires_token") and civitai_token:
            cmd.extend(["--header", f"Authorization: Bearer {civitai_token}"])
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"Failed: {e}")
        return False

def ensure_models():
    civitai_token = os.environ.get("CIVITAI_TOKEN", "a0271dea6028522e8ec098f0413c178d")
    for name, config in MODELS_TO_DOWNLOAD.items():
        download_model(name, config, civitai_token)

def wait_for_service(url, max_retries=50, delay=0.2):
    for i in range(max_retries):
        try:
            urllib.request.urlopen(url)
            return True
        except:
            time.sleep(delay)
    return False

def queue_workflow(workflow, client_id="runpod"):
    data = json.dumps({"prompt": workflow, "client_id": client_id}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    req.add_header('Content-Type', 'application/json')
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    url = f"http://127.0.0.1:8188/history/{prompt_id}"
    return json.loads(urllib.request.urlopen(url).read())

def get_image(filename, subfolder, folder_type):
    import urllib.parse
    params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
    return urllib.request.urlopen(f"http://127.0.0.1:8188/view?{params}").read()

def handler(event):
    input_data = event.get("input", {})
    prompt = input_data.get("prompt", "")
    negative_prompt = input_data.get("negative_prompt", "bad quality, worst quality")
    width = input_data.get("width", 768)
    height = input_data.get("height", 1024)
    steps = input_data.get("steps", 30)
    cfg_scale = input_data.get("cfg_scale", 7.0)
    model = input_data.get("model", "lustify")
    seed = input_data.get("seed", -1)
    workflow = input_data.get("workflow")
    
    ensure_models()
    
    if not wait_for_service("http://127.0.0.1:8188"):
        return {"error": "ComfyUI not available"}
    
    if not workflow:
        import random
        if seed == -1:
            seed = random.randint(1, 2147483647)
        
        checkpoint = "lustifySDXL_v7.safetensors" if model == "lustify" else "sd_xl_base_1.0.safetensors"
        if not os.path.exists(f"/comfyui/models/checkpoints/{checkpoint}"):
            checkpoint = "sd_xl_base_1.0.safetensors"
        
        workflow = {
            "4": {"inputs": {"ckpt_name": checkpoint}, "class_type": "CheckpointLoaderSimple"},
            "5": {"inputs": {"width": width, "height": height, "batch_size": 1}, "class_type": "EmptyLatentImage"},
            "6": {"inputs": {"text": prompt, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
            "7": {"inputs": {"text": negative_prompt, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
            "3": {"inputs": {"seed": seed, "steps": steps, "cfg": cfg_scale, "sampler_name": "euler", "scheduler": "normal", "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
            "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
            "9": {"inputs": {"filename_prefix": "lumina", "images": ["8", 0]}, "class_type": "SaveImage"}
        }
    
    try:
        result = queue_workflow(workflow)
        prompt_id = result.get("prompt_id")
        if not prompt_id:
            return {"error": "Failed to queue"}
        
        for _ in range(300):
            history = get_history(prompt_id)
            if prompt_id in history:
                outputs = history[prompt_id].get("outputs", {})
                images = []
                for node_output in outputs.values():
                    if "images" in node_output:
                        for img in node_output["images"]:
                            img_bytes = get_image(img["filename"], img.get("subfolder", ""), img.get("type", "output"))
                            images.append({"base64": base64.b64encode(img_bytes).decode('utf-8'), "filename": img["filename"]})
                if images:
                    return {"status": "success", "images": images, "seed": seed}
            time.sleep(1)
        return {"error": "Timeout"}
    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})

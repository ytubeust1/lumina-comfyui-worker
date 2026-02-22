import runpod
import json
import base64
import urllib.request
import time
import os

def wait_for_service(url, max_retries=50, delay=0.2):
    for i in range(max_retries):
        try:
            urllib.request.urlopen(url)
            return True
        except:
            time.sleep(delay)
    return False

def queue_workflow(workflow):
    data = json.dumps({"prompt": workflow}).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
    req.add_header('Content-Type', 'application/json')
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    return json.loads(urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}").read())

def get_image(filename, subfolder, folder_type):
    import urllib.parse
    params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
    return urllib.request.urlopen(f"http://127.0.0.1:8188/view?{params}").read()

def handler(event):
    input_data = event.get("input", {})
    prompt = input_data.get("prompt", "beautiful woman")
    negative_prompt = input_data.get("negative_prompt", "bad quality")
    width = input_data.get("width", 768)
    height = input_data.get("height", 1024)
    steps = input_data.get("steps", 25)
    cfg = input_data.get("cfg_scale", 7.0)
    seed = input_data.get("seed", -1)
    
    if seed == -1:
        import random
        seed = random.randint(1, 2147483647)
    
    if not wait_for_service("http://127.0.0.1:8188", max_retries=100):
        return {"error": "ComfyUI not ready"}
    
    workflow = {
        "3": {"inputs": {"seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "normal", "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
        "4": {"inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "5": {"inputs": {"width": width, "height": height, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        "6": {"inputs": {"text": prompt, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "7": {"inputs": {"text": negative_prompt, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"filename_prefix": "output", "images": ["8", 0]}, "class_type": "SaveImage"}
    }
    
    try:
        result = queue_workflow(workflow)
        prompt_id = result.get("prompt_id")
        
        for _ in range(120):
            history = get_history(prompt_id)
            if prompt_id in history:
                for node_output in history[prompt_id].get("outputs", {}).values():
                    if "images" in node_output:
                        images = []
                        for img in node_output["images"]:
                            img_bytes = get_image(img["filename"], img.get("subfolder", ""), img.get("type", "output"))
                            images.append({"base64": base64.b64encode(img_bytes).decode('utf-8')})
                        return {"status": "success", "images": images, "seed": seed}
            time.sleep(2)
        return {"error": "Timeout"}
    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})

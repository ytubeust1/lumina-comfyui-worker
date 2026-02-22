# Lumina AI - Custom ComfyUI Worker
# Base: RunPod's official ComfyUI SDXL worker
# Added: LUSTIFY, ReActor, IP-Adapter, AnimateDiff

FROM runpod/worker-comfyui:sdxl-1.1.0

WORKDIR /

# Install Python dependencies for face swap
RUN pip install --no-cache-dir insightface onnxruntime-gpu

# Create model directories
RUN mkdir -p /comfyui/models/checkpoints \
    /comfyui/models/loras \
    /comfyui/models/insightface \
    /comfyui/models/ipadapter \
    /comfyui/models/clip_vision \
    /comfyui/models/animatediff_models

# Clone custom nodes
RUN cd /comfyui/custom_nodes && \
    git clone https://github.com/Gourieff/comfyui-reactor-node.git && \
    git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git && \
    git clone https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git

# Install node requirements
RUN cd /comfyui/custom_nodes/comfyui-reactor-node && pip install -r requirements.txt || true

# Download models (these will be cached in the image)
# LUSTIFY V7 SDXL
ARG CIVITAI_TOKEN=""
RUN if [ -n "$CIVITAI_TOKEN" ]; then \
    wget -q --header="Authorization: Bearer ${CIVITAI_TOKEN}" \
    -O /comfyui/models/checkpoints/lustifySDXL_v7.safetensors \
    "https://civitai.com/api/download/models/708635?type=Model&format=SafeTensor"; \
    fi

# ReActor face swap model
RUN wget -q -O /comfyui/models/insightface/inswapper_128.onnx \
    "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/inswapper_128.onnx" || true

# IP-Adapter face model
RUN wget -q -O /comfyui/models/ipadapter/ip-adapter-plus-face_sdxl_vit-h.safetensors \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors" || true

# CLIP Vision for IP-Adapter
RUN wget -q -O /comfyui/models/clip_vision/CLIP-ViT-H-14.safetensors \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors" || true

# AnimateDiff motion model
RUN wget -q -O /comfyui/models/animatediff_models/v3_sd15_mm.ckpt \
    "https://huggingface.co/guoyww/animatediff/resolve/main/v3_sd15_mm.ckpt" || true

# Copy custom handler
COPY handler.py /handler.py

CMD ["python", "-u", "/handler.py"]

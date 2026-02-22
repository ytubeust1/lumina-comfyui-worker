FROM runpod/worker-comfyui:5.7.1-sdxl

WORKDIR /

RUN pip install --no-cache-dir insightface onnxruntime-gpu || true

RUN mkdir -p /comfyui/models/insightface \
    /comfyui/models/ipadapter \
    /comfyui/models/clip_vision \
    /comfyui/models/animatediff_models

ARG CIVITAI_TOKEN
RUN if [ -n "$CIVITAI_TOKEN" ]; then \
    wget -q --show-progress --header="Authorization: Bearer ${CIVITAI_TOKEN}" \
    -O /comfyui/models/checkpoints/lustifySDXL_v7.safetensors \
    "https://civitai.com/api/download/models/708635?type=Model&format=SafeTensor&size=pruned&fp=fp16"; \
    else echo "No CIVITAI_TOKEN provided, skipping LUSTIFY download"; fi

RUN cd /comfyui/custom_nodes && \
    ([ -d "comfyui-reactor-node" ] || git clone https://github.com/Gourieff/comfyui-reactor-node.git) && \
    ([ -d "ComfyUI_IPAdapter_plus" ] || git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus.git) && \
    ([ -d "ComfyUI-AnimateDiff-Evolved" ] || git clone https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git) && \
    ([ -d "ComfyUI-Manager" ] || git clone https://github.com/ltdrdata/ComfyUI-Manager.git) || true

RUN if [ -d "/comfyui/custom_nodes/comfyui-reactor-node" ]; then \
    cd /comfyui/custom_nodes/comfyui-reactor-node && pip install -r requirements.txt || true; \
    fi

RUN wget -q -O /comfyui/models/insightface/inswapper_128.onnx \
    "https://huggingface.co/datasets/Gourieff/ReActor/resolve/main/models/inswapper_128.onnx" || true

RUN wget -q -O /comfyui/models/ipadapter/ip-adapter-plus-face_sdxl_vit-h.safetensors \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors" || true

RUN wget -q -O /comfyui/models/clip_vision/CLIP-ViT-H-14.safetensors \
    "https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors" || true

RUN wget -q -O /comfyui/models/animatediff_models/v3_sd15_mm.ckpt \
    "https://huggingface.co/guoyww/animatediff/resolve/main/v3_sd15_mm.ckpt" || true

COPY handler.py /handler.py

CMD ["python", "-u", "/handler.py"]

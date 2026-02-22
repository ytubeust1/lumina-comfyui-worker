FROM runpod/worker-comfyui:5.7.1-sdxl

COPY handler.py /handler.py

CMD ["python", "-u", "/handler.py"]

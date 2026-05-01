import modal
import subprocess

app = modal.App("llm-qwen")

# === IMAGE DOCKER ===
vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.4.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.8.5",
        "transformers>=4.51.0,<5",
    )
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

MODEL_NAME = "Qwen/Qwen3-8B"
N_GPU = 1
VLLM_PORT = 8000
MINUTES = 60

@app.function(
    image=vllm_image,
    gpu="A10G",
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
    scaledown_window=15 * MINUTES,
    timeout=20 * MINUTES,
)
@modal.web_server(port=VLLM_PORT, startup_timeout=15 * MINUTES)
def serve():
    cmd = [
        "vllm", "serve", MODEL_NAME,
        "--served-model-name", "qwen",
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--tensor-parallel-size", str(N_GPU),
        "--max-model-len", "24000",        # 🚀 Ajusté à 24k pour passer sur A10G
        "--uvicorn-log-level", "info",
        "--enable-auto-tool-choice",
        "--tool-call-parser", "hermes",
        "--gpu-memory-utilization", "0.95", 
    ]

    print(f"🚀 Starting vLLM server with {MODEL_NAME} (24k context)...")
    subprocess.Popen(" ".join(cmd), shell=True)

@app.local_entrypoint()
def test():
    print("✅ Déploie avec: modal deploy app.py")
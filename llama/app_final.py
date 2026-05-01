import modal
import subprocess

app = modal.App("llm-llama-pro")

# === IMAGE DOCKER AVEC VLLM MODERNE (0.8.2) ===
# Cette version supporte le mode "strict" d'OpenClaw
vllm_image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "vllm==0.8.2", 
        "transformers==4.48.3",
        "numpy<2.0.0"
    )
    .env({
        "VLLM_ALLOW_LONG_MAX_MODEL_LEN": "1",
        "HF_XET_HIGH_PERFORMANCE": "1"
    })
)

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

# 🚀 MODÈLE : Llama 3.1 8B AWQ (Le plus stable pour les outils)
MODEL_NAME = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
VLLM_PORT = 8000

@app.function(
    image=vllm_image,
    gpu="A10G",
    volumes={"/root/.cache/huggingface": hf_cache_vol, "/root/.cache/vllm": vllm_cache_vol},
    timeout=3600,
)
@modal.web_server(port=VLLM_PORT, startup_timeout=600)
def serve():
    cmd = [
        "python3", "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL_NAME,
        "--served-model-name", "llama-awq",
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--max-model-len", "65536", 
        "--quantization", "awq",
        "--gpu-memory-utilization", "0.95",
        "--trust-remote-code",
        "--enable-auto-tool-choice",      # 🛡️ Crucial pour OpenClaw
        "--tool-call-parser", "llama3_json", # 🛡️ Crucial pour OpenClaw
        "--enforce-eager"
    ]

    print(f"🚀 Lancement Llama 3.1 AWQ (v0.8.2) - Prêt pour OpenClaw Strict")
    subprocess.Popen(cmd)

@app.local_entrypoint()
def test():
    print("✅ Déploiement : modal deploy app_final.py")
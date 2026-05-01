import modal
import subprocess

app = modal.App("llm-qwen-final")

# 🎯 ON PREND L'IMAGE OFFICIELLE ET ON NE TOUCHE À RIEN
# Comme on ne fait pas de .pip_install(), Modal ne cherchera pas 'python'
vllm_image = modal.Image.from_registry("vllm/vllm-openai:v0.7.2").env({
    "VLLM_ALLOW_LONG_MAX_MODEL_LEN": "1", # Autorise le 64k
    "HF_XET_HIGH_PERFORMANCE": "1"
})

hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct-AWQ"
VLLM_PORT = 8000

@app.function(
    image=vllm_image,
    gpu="A10G",
    volumes={"/root/.cache/huggingface": hf_cache_vol, "/root/.cache/vllm": vllm_cache_vol},
    timeout=3600,
)
@modal.web_server(port=VLLM_PORT, startup_timeout=600)
def serve():
    # On utilise directement les binaires de l'image vLLM
    cmd = [
        "python3", "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL_NAME,
        "--served-model-name", "qwen-awq",
        "--host", "0.0.0.0",
        "--port", str(VLLM_PORT),
        "--max-model-len", "65536",        # 🚀 OBJECTIF 64K
        "--quantization", "awq",
        "--kv-cache-dtype", "auto",
        "--tool-call-parser", "hermes",
        "--gpu-memory-utilization", "0.95",
        "--trust-remote-code",
        "--enforce-eager"
    ]

    print(f"🚀 Lancement de l'image officielle vLLM (64k context) - Mode Zero-Config")
    subprocess.Popen(cmd)

@app.local_entrypoint()
def test():
    print("✅ Déploiement : modal deploy app_awq.py")
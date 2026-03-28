import modal
import time
import subprocess
import socket
from fastapi.responses import JSONResponse, Response
from fastapi import Request
import json
import aiohttp

app = modal.App("llm-qwen")

# === 1. IMAGE DOCKER ===
vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.13.0",
        "huggingface_hub==0.36.0",
        "aiohttp",
    )
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)

# === 2. VOLUMES ===
CACHE_DIR = "/cache"
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)
hf_cache_vol = modal.Volume.from_name("huggingface-cache", create_if_missing=True)

volumes = {
    "/root/.cache/huggingface": hf_cache_vol,
    "/root/.cache/vllm": vllm_cache_vol,
}

# === 3. CONSTANTES ===
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
N_GPU = 1
VLLM_PORT = 8000
MINUTES = 60

def wait_for_server(proc, port=VLLM_PORT, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                return True
        except OSError:
            if proc.poll() is not None:
                raise RuntimeError(f"vLLM exited with code {proc.returncode}")
            time.sleep(1)
    raise TimeoutError("vLLM did not start in time")

# === 4. CLASSE AVEC UN SEUL ENDPOINT ===
@app.cls(
    image=vllm_image,
    gpu="A10G",
    volumes=volumes,
    timeout=10 * MINUTES,
    scaledown_window=5 * MINUTES,
)
@modal.concurrent(max_inputs=10)
class QwenLLM:
    @modal.enter()
    def start(self):
        print("🔄 Starting vLLM server with Qwen2.5-7B...")
        start_time = time.time()
        
        cmd = [
            "vllm",
            "serve",
            MODEL_NAME,
            "--served-model-name", "qwen",
            "--host", "0.0.0.0",
            "--port", str(VLLM_PORT),
            "--tensor-parallel-size", str(N_GPU),
            "--uvicorn-log-level", "info",
            "--max-model-len", "8192",
            "--gpu-memory-utilization", "0.9",
        ]
        
        print(" ".join(cmd))
        self.process = subprocess.Popen(cmd)
        wait_for_server(self.process)
        print(f"✅ vLLM ready in {time.time() - start_time:.1f}s")

    @modal.exit()
    def stop(self):
        if hasattr(self, 'process'):
            self.process.terminate()
            self.process.wait()

    # UN SEUL ENDPOINT : generate
    @modal.fastapi_endpoint(method="POST")
    async def generate(self, request: Request):
        try:
            body = await request.json()
            messages = body.get("messages", [])
            max_tokens = body.get("max_tokens", 512)
            temperature = body.get("temperature", 0.7)
            
            if not messages:
                return JSONResponse({"error": "messages required"}, status_code=400)
            
            payload = {
                "model": "qwen",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://localhost:{VLLM_PORT}/v1/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    result = await resp.json()
            
            return Response(
                content=json.dumps(result),
                media_type="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse({"error": str(e)}, status_code=500)

@app.local_entrypoint()
def test():
    print("✅ Code ready - deploy with: modal deploy app.py")
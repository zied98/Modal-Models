import modal
from io import BytesIO
import time
from fastapi.responses import JSONResponse, Response
from PIL import Image

app = modal.App("text-to-image-zimage")

# === IMAGE DOCKER AVEC LA DERNIÈRE VERSION DE DIFFUSERS ===
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install(
        "torch",
        "transformers",
        "accelerate",
        "pillow",
        "fastapi[standard]",
        "huggingface_hub",
    )
    # Installation de la dernière version de diffusers depuis le main
    .run_commands(
        "pip install git+https://github.com/huggingface/diffusers.git"
    )
)

# === VOLUME ===
CACHE_DIR = "/cache"
cache_volume = modal.Volume.from_name("zimage-cache", create_if_missing=True)
volumes = {CACHE_DIR: cache_volume}

# === ENVIRONNEMENT ===
image = image.env({
    "HF_HOME": CACHE_DIR,
    "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"
})

with image.imports():
    import torch
    # Le nom correct est probablement ZImagePipeline
    from diffusers import ZImagePipeline

@app.cls(
    image=image,
    gpu="A10G",
    volumes=volumes,
    scaledown_window=60 * 2,
    timeout=1800,
)
class ZImageTextToImage:
    @modal.enter()
    def load(self):
        print("🔄 Chargement de Z-Image-Turbo...", flush=True)
        start = time.time()
        
        # Vérifions ce qui est disponible
        print("🔍 Vérification des pipelines disponibles...", flush=True)
        
        self.pipe = ZImagePipeline.from_pretrained(
            "Tongyi-MAI/Z-Image-Turbo",
            torch_dtype=torch.bfloat16,
            cache_dir=CACHE_DIR,
            low_cpu_mem_usage=True,
        )
        self.pipe.enable_model_cpu_offload()
        
        elapsed = time.time() - start
        print(f"✅ Chargé en {elapsed:.1f}s", flush=True)

    @modal.method()
    def generate(self, prompt: str, height: int = 512, width: int = 512) -> bytes:
        generator = torch.Generator(device="cuda").manual_seed(42)
        
        result = self.pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_inference_steps=8,
            guidance_scale=0.0,
            generator=generator,
        ).images[0]
        
        output = BytesIO()
        result.save(output, format="PNG")
        return output.getvalue()

    @modal.fastapi_endpoint(method="POST")
    def generate_image(self, prompt: str, height: int = 512, width: int = 512):
        try:
            if not prompt:
                return JSONResponse(
                    {"error": "Prompt requis"},
                    status_code=400,
                    headers={"Access-Control-Allow-Origin": "*"}
                )
            
            height = ((max(256, min(1024, height))) // 8) * 8
            width = ((max(256, min(1024, width))) // 8) * 8
            
            print(f"📝 Génération: {prompt[:100]}...", flush=True)
            start = time.time()
            result_bytes = self.generate.local(prompt, height, width)
            elapsed = time.time() - start
            
            return Response(
                content=result_bytes,
                media_type="image/png",
                headers={"Access-Control-Allow-Origin": "*"}
            )
            
        except Exception as e:
            print(f"❌ Erreur: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return JSONResponse(
                {"error": str(e)},
                status_code=500,
                headers={"Access-Control-Allow-Origin": "*"}
            )

    @modal.fastapi_endpoint(method="GET")
    def health(self):
        return {"status": "ok", "model": "Z-Image-Turbo"}

@app.local_entrypoint()
def test():
    print("✅ Code prêt")
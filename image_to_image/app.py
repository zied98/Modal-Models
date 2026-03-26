import modal
from io import BytesIO
import base64
from fastapi.responses import JSONResponse, Response
from PIL import Image
from typing import Optional

app = modal.App("image-to-image-flux-klein")

# === 1. IMAGE ===
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install(
        "torch",
        "transformers",
        "git+https://github.com/huggingface/diffusers.git",
        "accelerate",
        "pillow",
        "fastapi[standard]",
        "huggingface_hub",
    )
)

# === 2. VOLUME ===
CACHE_DIR = "/cache"
cache_volume = modal.Volume.from_name("flux-klein-cache", create_if_missing=True)
volumes = {CACHE_DIR: cache_volume}

# === 3. ENVIRONNEMENT ===
image = image.env({
    "HF_HOME": CACHE_DIR,
    "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"
})

# === 4. IMPORTS ===
with image.imports():
    import torch
    from diffusers import Flux2KleinPipeline

# === 5. CLASSE ===
@app.cls(
    image=image,
    gpu="A10G",
    volumes=volumes,
    scaledown_window=60 * 2,
)
@modal.concurrent(max_inputs=2)
class FluxKleinEditor:
    @modal.enter()
    def load(self):
        print("🔄 Chargement de FLUX.2-klein...")
        self.pipe = Flux2KleinPipeline.from_pretrained(
            "black-forest-labs/FLUX.2-klein-base-4B",
            torch_dtype=torch.bfloat16,
            cache_dir=CACHE_DIR,
        )
        self.pipe.enable_model_cpu_offload()
        print("✅ Modèle FLUX.2-klein chargé")

    @modal.method()
    def edit(self, image_bytes: bytes, prompt: str, guidance: float = 4.0) -> bytes:
        input_image = Image.open(BytesIO(image_bytes)).convert("RGB")
        
        result = self.pipe(
            prompt=prompt,
            image=input_image,
            num_inference_steps=28,
            guidance_scale=guidance,
            height=512,
            width=512,
            generator=torch.Generator(device="cuda").manual_seed(42),
        ).images[0]
        
        output = BytesIO()
        result.save(output, format="PNG")
        return output.getvalue()

    # UN SEUL ENDPOINT : generate (POST)
    @modal.fastapi_endpoint(method="POST")
    async def generate(
        self,
        prompt: str,
        image_data: Optional[str] = None
    ):
        try:
            if not prompt:
                return JSONResponse(
                    {"error": "Prompt requis"},
                    status_code=400,
                    headers={"Access-Control-Allow-Origin": "*"}
                )
            
            # Si pas d'image, créer une image grise par défaut
            if not image_data:
                img = Image.new('RGB', (512, 512), color='gray')
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                image_bytes = buffer.getvalue()
            else:
                if image_data.startswith("data:image"):
                    image_bytes = base64.b64decode(image_data.split(",")[1])
                else:
                    image_bytes = base64.b64decode(image_data)
            
            result_bytes = self.edit.local(image_bytes, prompt)
            
            return Response(
                content=result_bytes,
                media_type="image/png",
                headers={"Access-Control-Allow-Origin": "*"}
            )
            
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=500,
                headers={"Access-Control-Allow-Origin": "*"}
            )

@app.local_entrypoint()
def test():
    print("✅ API FLUX.2-klein prête")
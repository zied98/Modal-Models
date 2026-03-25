import modal
import time
import random
from pathlib import Path
from fastapi.responses import JSONResponse, Response
from fastapi import Request

app = modal.App("video-generation-wan")

# === 1. IMAGE DOCKER ===
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ffmpeg")
    .pip_install(
        "torch",
        "transformers",
        "accelerate",
        "pillow",
        "fastapi[standard]",
        "huggingface_hub",
        "imageio",
        "imageio-ffmpeg",
        "numpy",
    )
    .run_commands(
        "pip install git+https://github.com/huggingface/diffusers.git"
    )
)

# === 2. VOLUMES ===
CACHE_DIR = "/cache"
OUTPUT_DIR = "/outputs"

cache_volume = modal.Volume.from_name("wan-cache", create_if_missing=True)
output_volume = modal.Volume.from_name("wan-outputs", create_if_missing=True)

volumes = {
    CACHE_DIR: cache_volume,
    OUTPUT_DIR: output_volume,
}

# === 3. ENVIRONNEMENT ===
image = image.env({
    "HF_HOME": CACHE_DIR,
    "HF_HUB_CACHE": CACHE_DIR,
})

# === 4. IMPORTS ===
with image.imports():
    import torch
    from diffusers import WanPipeline, AutoencoderKLWan
    from diffusers.utils import export_to_video

# === 5. CONSTANTES ===
MODEL_ID = "Wan-AI/Wan2.2-T2V-A14B-Diffusers"

# === 6. CLASSE ===
@app.cls(
    image=image,
    gpu="H100",
    volumes=volumes,
    timeout=1800,
    scaledown_window=60 * 10,
)
@modal.concurrent(max_inputs=1)
class WanVideoGenerator:
    @modal.enter()
    def load(self):
        print("🔄 Chargement de Wan2.2...")
        start = time.time()
        
        self.vae = AutoencoderKLWan.from_pretrained(
            MODEL_ID,
            subfolder="vae",
            torch_dtype=torch.float32,
            cache_dir=CACHE_DIR,
        )
        
        self.pipe = WanPipeline.from_pretrained(
            MODEL_ID,
            vae=self.vae,
            torch_dtype=torch.bfloat16,
            cache_dir=CACHE_DIR,
        )
        self.pipe.to("cuda")
        print(f"✅ Chargé en {time.time()-start:.1f}s")

    @modal.method()
    def generate(self, prompt: str, height: int = 480, width: int = 720, 
                 num_frames: int = 81, seed: int = None) -> str:
        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        
        generator = torch.Generator(device="cuda").manual_seed(seed)
        
        output = self.pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_frames=num_frames,
            num_inference_steps=40,
            guidance_scale=4.0,
            generator=generator,
        )
        
        safe_prompt = "".join(c if c.isalnum() or c == " " else "_" for c in prompt[:50])
        mp4_name = f"{seed}_{safe_prompt.replace(' ', '_')}.mp4"
        
        export_to_video(output.frames[0], Path(OUTPUT_DIR) / mp4_name, fps=16)
        output_volume.commit()
        torch.cuda.empty_cache()
        return mp4_name

    @modal.fastapi_endpoint(method="POST")
    async def generate_video(self, request: Request):
        try:
            # Récupérer le prompt depuis l'URL ou le body
            params = request.query_params
            prompt = params.get("prompt")
            
            if not prompt:
                form = await request.form()
                prompt = form.get("prompt")
            
            if not prompt:
                return JSONResponse({"error": "Prompt requis"}, status_code=400)
            
            height = int(params.get("height", 480))
            width = int(params.get("width", 720))
            num_frames = int(params.get("num_frames", 81))
            
            print(f"📝 Génération: {prompt[:50]}...")
            start = time.time()
            
            mp4_name = self.generate.local(prompt, height, width, num_frames)
            
            # Lire le fichier depuis le volume
            video_bytes = b"".join(output_volume.read_file(mp4_name))
            
            print(f"✅ Généré en {time.time()-start:.1f}s, {len(video_bytes)} bytes")
            
            return Response(
                content=video_bytes,
                media_type="video/mp4",
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Content-Disposition": f"attachment; filename={mp4_name}",
                    "Content-Length": str(len(video_bytes))
                }
            )
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse({"error": str(e)}, status_code=500)

@app.local_entrypoint()
def test():
    print("✅ Code prêt")
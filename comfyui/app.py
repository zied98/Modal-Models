import modal
import subprocess
import time
import socket
import os

app = modal.App("comfyui-server")

# === 1. IMAGE DOCKER ===
comfyui_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ffmpeg", "libgl1-mesa-glx", "libglib2.0-0")
    .pip_install(
        "torch",
        "torchvision",
        "torchaudio",
        "numpy",
        "pillow",
        "fastapi[standard]",
        "aiohttp",
    )
    .run_commands(
        # Cloner ComfyUI
        "git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui",
        # Installer les dépendances
        "cd /comfyui && pip install -r requirements.txt",
        # Créer les dossiers de montage
        "mkdir -p /models /output",
        # Créer des liens symboliques vers les dossiers de montage
        "rm -rf /comfyui/models && ln -s /models /comfyui/models",
        "rm -rf /comfyui/output && ln -s /output /comfyui/output",
    )
)

# === 2. VOLUMES ===
MODELS_VOLUME = modal.Volume.from_name("comfyui-models", create_if_missing=True)
OUTPUT_VOLUME = modal.Volume.from_name("comfyui-outputs", create_if_missing=True)

volumes = {
    "/models": MODELS_VOLUME,
    "/output": OUTPUT_VOLUME,
}

# === 3. CONSTANTES ===
COMFYUI_PORT = 8188
MINUTES = 60

def wait_for_server(port=COMFYUI_PORT, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=2):
                return True
        except OSError:
            time.sleep(2)
    raise TimeoutError("ComfyUI n'a pas démarré")

# === 4. CLASSE AVEC UN SEUL ENDPOINT ===
@app.cls(
    image=comfyui_image,
    gpu="A10G",
    volumes=volumes,
    timeout=10 * MINUTES,
    scaledown_window=5 * MINUTES,
)
@modal.concurrent(max_inputs=5)
class ComfyUIServer:
    @modal.enter()
    def start(self):
        print("🚀 Démarrage de ComfyUI...")
        start_time = time.time()
        
        cmd = [
            "python", "/comfyui/main.py",
            "--listen", "0.0.0.0",
            "--port", str(COMFYUI_PORT),
            "--dont-print-server",
        ]
        
        print(" ".join(cmd))
        self.process = subprocess.Popen(cmd, cwd="/comfyui")
        wait_for_server(COMFYUI_PORT)
        print(f"✅ ComfyUI prêt en {time.time() - start_time:.1f}s")

    @modal.exit()
    def stop(self):
        if hasattr(self, 'process'):
            self.process.terminate()
            self.process.wait()

    # UN SEUL ENDPOINT : l'interface graphique
    @modal.web_server(port=COMFYUI_PORT, startup_timeout=10 * MINUTES)
    def ui(self):
        """Interface graphique ComfyUI avec les nœuds"""
        pass

@app.local_entrypoint()
def test():
    print("✅ Code prêt - 1 seul endpoint (interface graphique)")
    print("📌 Déploiement: modal deploy app.py")
    print("📌 Ouvre l'URL https://...-ui.modal.run dans ton navigateur")
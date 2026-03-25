from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import json
import urllib.parse
import urllib.request

API_URL = "https://ziedbouzekri06--video-generation-wan-wanvideogenerator-g-0a47a6.modal.run"

class VideoHelperHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/list':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            result = subprocess.run(
                ["python", "download_helper.py", "--list"],
                capture_output=True,
                text=True
            )
            
            videos = []
            for line in result.stdout.split('\n'):
                if '.mp4' in line and ' - ' in line:
                    filename = line.split(' - ')[0].strip()
                    videos.append(filename)
            
            self.wfile.write(json.dumps(videos).encode())
    
    def do_POST(self):
        # Gestion de la génération de vidéo
        if self.path == '/generate':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(body)
            
            prompt = params.get('prompt', [''])[0]
            height = params.get('height', ['480'])[0]
            width = params.get('width', ['720'])[0]
            num_frames = params.get('num_frames', ['81'])[0]
            
            print(f"📝 Génération: {prompt[:50]}...")
            
            # Appeler l'API Modal
            url = f"{API_URL}?prompt={urllib.parse.quote(prompt)}&height={height}&width={width}&num_frames={num_frames}"
            req = urllib.request.Request(url, method='POST')
            
            try:
                with urllib.request.urlopen(req, timeout=600) as response:
                    video_data = response.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'video/mp4')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(video_data)
                
            except Exception as e:
                print(f"❌ Erreur: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        
        # Gestion du téléchargement
        elif self.path == '/download':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            result = subprocess.run(
                ["python", "download_helper.py", "--latest"],
                capture_output=True,
                text=True
            )
            
            success = result.returncode == 0
            self.wfile.write(json.dumps({"success": success, "output": result.stdout}).encode())
    
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

if __name__ == '__main__':
    port = 8002
    print(f"🚀 Helper server démarré sur http://localhost:{port}")
    print(f"🔗 Relay vers: {API_URL}")
    print("Appuyez sur Ctrl+C pour arrêter")
    httpd = HTTPServer(('localhost', port), VideoHelperHandler)
    httpd.serve_forever()
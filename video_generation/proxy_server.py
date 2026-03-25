from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import json
import sys

API_URL = "https://ziedbouzekri06--video-generation-wan-wanvideogenerator-g-0a47a6.modal.run"

class ProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        try:
            # Lire le body de la requête de l'UI
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            # Extraire les paramètres
            params = urllib.parse.parse_qs(body)
            prompt = params.get('prompt', [''])[0]
            height = params.get('height', ['480'])[0]
            width = params.get('width', ['720'])[0]
            num_frames = params.get('num_frames', ['81'])[0]
            seed = params.get('seed', [None])[0]
            
            print(f"📝 Prompt reçu: {prompt[:50]}...")
            
            if not prompt:
                self.send_error(400, "Prompt requis")
                return
            
            # Construire l'URL avec les paramètres
            url_params = {
                'prompt': prompt,
                'height': height,
                'width': width,
                'num_frames': num_frames
            }
            if seed and seed != 'None':
                url_params['seed'] = seed
            
            url = f"{API_URL}?{urllib.parse.urlencode(url_params)}"
            
            print(f"📤 Appel API: {url[:120]}...")
            
            # Utiliser POST (pas GET) - c'est ce qui fonctionnait avec curl
            req = urllib.request.Request(url, method='POST')
            with urllib.request.urlopen(req, timeout=600) as response:
                video_data = response.read()
            
            print(f"✅ Vidéo reçue: {len(video_data)} bytes")
            
            # Retourner la vidéo à l'UI
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp4')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(video_data)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

if __name__ == '__main__':
    port = 8001
    print(f"🚀 Proxy démarré sur http://localhost:{port}")
    print(f"🔗 Relay vers: {API_URL}")
    print("Appuyez sur Ctrl+C pour arrêter")
    httpd = HTTPServer(('localhost', port), ProxyHandler)
    httpd.serve_forever()
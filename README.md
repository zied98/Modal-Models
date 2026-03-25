\# 🎨 Chatterbox Géopolitique - Suite IA



Suite de modèles d'intelligence artificielle déployés sur Modal.



\## 📦 Modèles disponibles



| Modèle | Type | Dossier |

|--------|------|---------|

| Text-to-Speech | Génération vocale | `tts/` |

| Text-to-Image | Z-Image-Turbo | `text\_to\_image/` |

| Image-to-Image | FLUX.2-klein | `image\_to\_image/` |

| Text-to-Video | Wan2.2 | `video\_generation/` |



\## 🚀 Déploiement



Chaque modèle est indépendant et se déploie séparément :



```bash

cd tts

modal deploy app.py



cd ../text\_to\_image

modal deploy app.py



\# etc.


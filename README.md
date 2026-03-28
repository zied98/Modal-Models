## 📄 Fichier `README.md` (documentation complète)

```markdown
# 🎨 AI Studio - Suite de modèles IA

Suite complète de modèles d'intelligence artificielle déployés sur [Modal](https://modal.com) pour la génération de texte, d'images, de vidéos et de parole.

## 📦 Modèles disponibles

| Modèle | Type | Description |
|--------|------|-------------|
| **Text-to-Speech** | Vocal | Génération de parole à partir de texte (20+ voix) |
| **Text-to-Image** | Image | Génération d'images avec Z-Image-Turbo |
| **Image-to-Image** | Édition | Transformation d'images avec FLUX.2-klein |
| **Text-to-Video** | Vidéo | Génération de vidéos avec Wan2.2 |
| **LLM Assistant** | Texte | Assistant conversationnel Qwen2.5-7B |
| **ComfyUI** | Workflow | Interface graphique pour workflows IA |

## 🏗️ Structure du projet

```
chatterbox_geopolitique/
├── index.html                 # Dashboard principal
├── tts/                       # Text-to-Speech
│   ├── app.py                 # Déploiement Modal
│   ├── tts_ui.html            # Interface utilisateur
│   └── generations/           # Audios générés
├── text_to_image/             # Text-to-Image
│   ├── app.py
│   ├── text_to_image_ui.html
│   └── generations/
├── image_to_image/            # Image-to-Image
│   ├── app.py
│   ├── image_ui.html
│   └── transformations/
├── video_generation/          # Text-to-Video
│   ├── app.py
│   ├── video_ui.html
│   ├── proxy_server.py        # Proxy local (optionnel)
│   └── generations/
├── llm/                       # Assistant LLM
│   ├── app.py
│   ├── llm_ui.html
│   └── conversations/
├── comfyui/                   # ComfyUI
│   ├── app.py                 # Serveur ComfyUI
│   └── workflows/             # Workflows pré-définis
└── dashboard/                 # (optionnel)
```

## 🚀 Déploiement

### Prérequis

- Un compte [Modal](https://modal.com)
- Python 3.11 ou supérieur
- `modal` installé (`pip install modal`)

### Variables d'environnement

```bash
# Hugging Face token (optionnel mais recommandé)
export HF_TOKEN="votre_token_ici"
```

### Déployer un modèle

```bash
# Exemple pour le LLM
cd llm
modal deploy app.py

# Les autres modèles suivent le même principe
cd ../tts && modal deploy app.py
cd ../text_to_image && modal deploy app.py
cd ../image_to_image && modal deploy app.py
cd ../video_generation && modal deploy app.py
cd ../comfyui && modal deploy app.py
```

## 🖥️ Utilisation

### Interface Web

Le dashboard principal (`index.html`) donne accès à toutes les interfaces :

1. Ouvrez `index.html` dans votre navigateur
2. Cliquez sur la carte du modèle souhaité
3. Utilisez l'interface dédiée

### API (cURL)

Chaque modèle expose un endpoint unique. Exemple pour le LLM :

```bash
curl -X POST https://[URL].modal.run \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 100}'
```

### Récupération des vidéos (Wan2.2)

```bash
# Lister les vidéos disponibles
python -m modal volume ls wan-outputs

# Télécharger une vidéo
python -m modal volume get wan-outputs [NOM_FICHIER] generations/video.mp4
```

## 🔧 Configuration

### Hardware

| Modèle | GPU | VRAM |
|--------|-----|------|
| TTS | A10G | 24 GB |
| Text-to-Image | A10G | 24 GB |
| Image-to-Image | A10G | 24 GB |
| Video | H100 | 80 GB |
| LLM | A10G | 24 GB |
| ComfyUI | A10G | 24 GB |

### Volumes persistants

| Volume | Contenu |
|--------|---------|
| `flux-klein-cache` | Modèles FLUX |
| `zimage-cache` | Modèles Z-Image |
| `wan-cache` | Modèles Wan2.2 |
| `wan-outputs` | Vidéos générées |
| `vllm-cache` | Cache vLLM |
| `huggingface-cache` | Modèles Hugging Face |
| `comfyui-models` | Modèles ComfyUI |
| `comfyui-outputs` | Sorties ComfyUI |

## 📝 Gestion des secrets

Les tokens Hugging Face sont gérés via les secrets Modal :

```bash
modal secret create huggingface-secret HF_TOKEN=votre_token
```

## 🌐 Déploiement web (Netlify)

1. Poussez le projet sur GitHub
2. Connectez votre dépôt sur Netlify
3. Déployez avec les paramètres par défaut

## 🧹 Nettoyage

### Supprimer les applications inutilisées

```bash
modal app list
modal app stop [APP_ID]
```

### Nettoyer les volumes

```bash
modal volume ls [VOLUME_NAME]
modal volume rm [VOLUME_NAME] [FILENAME]
```

## 📄 Licence

Ce projet est sous licence MIT.

## 🤝 Contribution

Les contributions sont les bienvenues ! Merci de suivre les bonnes pratiques de développement.

## 📧 Contact

Pour toute question, ouvrez une issue sur GitHub.

---

**Note :** Les URLs des API sont générées lors du déploiement et doivent être configurées dans les fichiers HTML respectifs.
```

## 📝 Comment ajouter les URLs localement

Crée un fichier `.env.local` (ne pas commit sur GitHub) :

```bash
# URLs Modal (à remplacer par vos URLs)
TTS_URL=https://...modal.run
TEXT2IMG_URL=https://...modal.run
IMG2IMG_URL=https://...modal.run
VIDEO_URL=https://...modal.run
LLM_URL=https://...modal.run
COMFYUI_URL=https://...modal.run
```

## 🚀 Pousser sur GitHub

```bash
# 1. Ajouter le README
git add README.md

# 2. Vérifier que .gitignore exclut les fichiers sensibles
cat .gitignore
# Doit contenir :
# .env.local
# hf_token.txt

# 3. Commiter
git commit -m "Add comprehensive README documentation"

# 4. Pousser
git push origin main
```

## ✅ Vérification

```bash
# Vérifier que les fichiers sensibles ne sont pas commités
git status
# Ne doit pas montrer .env.local ou hf_token.txt
```

**Le README est prêt ! Pousse-le et partage-moi le lien de ton dépôt GitHub si tu veux.**
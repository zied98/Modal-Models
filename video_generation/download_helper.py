#!/usr/bin/env python3
"""
Helper script to download the latest video from Modal volume.
Usage: python download_helper.py
"""

import subprocess
import sys
import os
import re
from datetime import datetime

# Configuration
VOLUME_NAME = "wan-outputs"
OUTPUT_DIR = "generations"

def get_latest_video():
    """Get the filename of the latest video in the volume"""
    try:
        # Run modal volume ls command
        result = subprocess.run(
            ["python", "-m", "modal", "volume", "ls", VOLUME_NAME],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"❌ Erreur: {result.stderr}")
            return None
        
        # Parse output to find the latest .mp4 file
        lines = result.stdout.split('\n')
        latest_file = None
        latest_time = None
        
        for line in lines:
            if '.mp4' not in line:
                continue
            
            # Extract filename and date
            parts = line.split('│')
            if len(parts) >= 3:
                filename = parts[1].strip()
                date_info = parts[3].strip() if len(parts) > 3 else ''
                
                # Simple heuristic: take the first .mp4 file (usually the latest)
                # Modal lists files in order, newest first
                if filename and filename.endswith('.mp4'):
                    return filename
        
        return latest_file
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def download_video(filename):
    """Download a specific video from the volume"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{timestamp}_{filename}"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Download the file
        print(f"📥 Téléchargement de {filename}...")
        result = subprocess.run(
            ["python", "-m", "modal", "volume", "get", VOLUME_NAME, filename, output_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"❌ Erreur de téléchargement: {result.stderr}")
            return None
        
        print(f"✅ Vidéo téléchargée: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def list_videos():
    """List all videos in the volume"""
    try:
        result = subprocess.run(
            ["python", "-m", "modal", "volume", "ls", VOLUME_NAME],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"❌ Erreur: {result.stderr}")
            return []
        
        videos = []
        lines = result.stdout.split('\n')
        for line in lines:
            if '.mp4' in line:
                parts = line.split('│')
                if len(parts) >= 3:
                    filename = parts[1].strip()
                    if filename:
                        videos.append(filename)
        return videos
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download videos from Modal volume")
    parser.add_argument("--list", action="store_true", help="List all videos")
    parser.add_argument("--latest", action="store_true", help="Download the latest video")
    parser.add_argument("--filename", type=str, help="Download a specific video by filename")
    
    args = parser.parse_args()
    
    if args.list:
        videos = list_videos()
        print("📁 Vidéos disponibles:")
        for v in videos:
            print(f"  - {v}")
    
    elif args.latest:
        filename = get_latest_video()
        if filename:
            download_video(filename)
        else:
            print("❌ Aucune vidéo trouvée")
    
    elif args.filename:
        download_video(args.filename)
    
    else:
        # Default: download latest
        filename = get_latest_video()
        if filename:
            download_video(filename)
        else:
            print("❌ Aucune vidéo trouvée")
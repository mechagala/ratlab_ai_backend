#!/usr/bin/env python3
"""
Script para convertir clips existentes a formato compatible con navegadores web.
Usa FFmpeg con -movflags +faststart para permitir streaming progresivo.
"""
import os
import subprocess
import sys

def convert_clip(input_path):
    """Convierte un clip a formato web-compatible."""
    temp_path = input_path + '.temp.mp4'
    
    cmd = [
        'ffmpeg',
        '-y',
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-an',
        temp_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            os.replace(temp_path, input_path)
            return True
        else:
            print(f"  Error FFmpeg: {result.stderr[:200]}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    except Exception as e:
        print(f"  Excepción: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def main():
    # Buscar todos los directorios de clips en experiments
    base_path = '/ratlab_ai_backend/media/experiments'
    
    if not os.path.exists(base_path):
        print(f"Directorio no encontrado: {base_path}")
        sys.exit(1)
    
    converted = 0
    failed = 0
    
    for exp_id in os.listdir(base_path):
        clips_dir = os.path.join(base_path, exp_id, 'clips')
        if not os.path.isdir(clips_dir):
            continue
            
        print(f"\n=== Experimento {exp_id} ===")
        
        for filename in os.listdir(clips_dir):
            if filename.endswith('.mp4') and not filename.endswith('_temp.mp4'):
                filepath = os.path.join(clips_dir, filename)
                print(f"Convirtiendo: {filename}...", end=' ')
                
                if convert_clip(filepath):
                    print("OK")
                    converted += 1
                else:
                    print("FAILED")
                    failed += 1
    
    print(f"\n=== Resumen ===")
    print(f"Convertidos: {converted}")
    print(f"Fallidos: {failed}")

if __name__ == '__main__':
    main()


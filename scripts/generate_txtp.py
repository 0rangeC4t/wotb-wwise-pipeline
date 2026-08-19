import subprocess
import os
import argparse
import re
import json
import shutil

def generate_txtp():
    parser = argparse.ArgumentParser(description="Generate .txtp files using wwiser.")
    parser.add_argument('--input', default='input/WwiseSound', help='Input WwiseSound directory')
    parser.add_argument('--output', default='out_wwise/txtp', help='Output directory for generated txtp files')
    parser.add_argument('--wemdir', default='pool', help='Directory containing carved .wem files')
    parser.add_argument('--manifest', default='manifest.json', help='Path to manifest.json (for dynamic language detection)')
    args = parser.parse_args()

    wwiser_py = 'tools/wwiser/wwiser.py'
    input_dir = args.input
    out_dir = args.output
    pool_dir = args.wemdir
    os.makedirs(out_dir, exist_ok=True)

    # Dynamic language detection from manifest.json — replaces hardcoded crewvoice_langs.
    # Collect all non-empty language values from manifest (which are now always lists).
    known_langs = set()
    manifest_path = args.manifest
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
        for entry in manifest_data.values():
            lang_val = entry.get("language", [])
            if isinstance(lang_val, list):
                known_langs.update(lang_val)
            elif lang_val is not None:
                # Backward compat: handle old single-string format if encountered
                known_langs.add(lang_val)
        print(f"Loaded {len(known_langs)} languages from manifest: {sorted(known_langs)}")
    else:
        # Fallback: scan input dir for subdirectories containing .bnk files
        print(f"Warning: manifest not found at {manifest_path}, falling back to directory scan for languages")
        for entry in os.listdir(input_dir):
            subdir = os.path.join(input_dir, entry)
            if os.path.isdir(subdir) and any(f.endswith('.bnk') for f in os.listdir(subdir)):
                known_langs.add(entry)
        print(f"Detected {len(known_langs)} language dirs from input: {sorted(known_langs)}")

    # Ensure SoundbanksInfo.json and PluginInfo.json are copied/symlinked into every localized subdirectory
    # so that wwiser can find companion name info when parsing localized banks
    main_info = os.path.join(input_dir, 'SoundbanksInfo.json')
    main_plugin = os.path.join(input_dir, 'PluginInfo.json')
    for root, dirs, files in os.walk(input_dir):
        if root == input_dir:
            continue
        if any(f.endswith('.bnk') for f in files):
            for json_file in [main_info, main_plugin]:
                if os.path.exists(json_file):
                    dest_json = os.path.join(root, os.path.basename(json_file))
                    if not os.path.exists(dest_json):
                        try:
                            os.symlink(os.path.abspath(json_file), dest_json)
                        except Exception:
                            shutil.copy(json_file, dest_json)
    
    # We recursively find bnk files.
    bnk_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.bnk'):
                bnk_files.append(os.path.join(root, file))
                
    print(f"Found {len(bnk_files)} bnk files to generate .txtp routing...")
    
    # Keep pool/ 100% clean as designed. We create a separate consolidated directory
    # out_wwise/render_pool for wwiser and vgmstream path resolution.
    render_pool = os.path.join(os.path.dirname(out_dir), 'render_pool')
    os.makedirs(render_pool, exist_ok=True)
    
    # 1. Symlink or copy all .wem files from pool_dir into render_pool
    if os.path.exists(pool_dir):
        for f in os.listdir(pool_dir):
            if f.endswith('.wem'):
                src_wem = os.path.join(pool_dir, f)
                dest_wem = os.path.join(render_pool, f)
                if not os.path.exists(dest_wem):
                    try:
                        os.symlink(os.path.abspath(src_wem), dest_wem)
                    except Exception:
                        shutil.copy(src_wem, dest_wem)

    # 2. Symlink or copy all .bnk files into render_pool so vgmstream can resolve them
    # We preserve the relative directory structure to avoid name collisions (e.g. voiceover_crew.bnk)
    for bnk in bnk_files:
        rel_path = os.path.relpath(bnk, input_dir)
        dest = os.path.join(render_pool, rel_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if not os.path.exists(dest):
            try:
                os.symlink(os.path.abspath(bnk), dest)
            except Exception:
                shutil.copy(bnk, dest)

    print(f"Running wwiser on {len(bnk_files)} banks individually...")
    for idx, bnk in enumerate(bnk_files, 1):
        rel_path = os.path.relpath(bnk, input_dir)
        parts = rel_path.split(os.sep)
        
        # Detect language from subdirectory name using dynamically loaded languages
        lang = None
        if len(parts) > 1 and parts[0] in known_langs:
            lang = parts[0]
            
        cmd = ['python3', wwiser_py]
        if lang:
            cmd += ['-gl', lang]
            # Use lang-specific render_pool subdir so wwiser writes the correct
            # per-lang path (render_pool/<lang>/voiceover_crew.bnk) into txtp.
            # That subdir is already symlinked by the bnk-copy loop above.
            lang_wemdir = os.path.abspath(os.path.join(render_pool, lang))
            cmd += ['-g', '-gd', '-go', out_dir, '-gw', lang_wemdir]
        else:
            cmd += ['-g', '-gd', '-go', out_dir, '-gw', os.path.abspath(render_pool)]
        cmd += [bnk]
        
        print(f"[{idx}/{len(bnk_files)}] Processing {rel_path} (lang={lang})...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"  STDOUT: {result.stdout.strip()}")
        if result.stderr.strip():
            print(f"  STDERR: {result.stderr.strip()}")
        if result.returncode != 0:
            print(f"wwiser txtp generation failed for {bnk} with code {result.returncode}")

    print("wwiser txtp generation complete. Organizing crewvoice languages...")
    moved_count = 0
    for root, dirs, files in os.walk(out_dir):
        if "crewvoice" in dirs:
            dirs.remove("crewvoice")  # Don't descend into already organized crewvoice folder
        
        for file in files:
            if file.endswith('.txtp'):
                match = re.search(r'\{l=([a-zA-Z()_]+)\}', file)
                if match:
                    lang = match.group(1)
                    # Use dynamically loaded languages instead of hardcoded set
                    if lang in known_langs:
                        target_dir = os.path.join(out_dir, "crewvoice", lang)
                        os.makedirs(target_dir, exist_ok=True)
                        
                        src_path = os.path.join(root, file)
                        dest_path = os.path.join(target_dir, file)
                        if src_path != dest_path:
                            shutil.move(src_path, dest_path)
                            moved_count += 1
    print(f"Crewvoice organization complete. Moved {moved_count} files.")

if __name__ == '__main__':
    generate_txtp()

import subprocess
import os
import argparse
import re
import shutil

def generate_txtp():
    parser = argparse.ArgumentParser(description="Generate .txtp files using wwiser.")
    parser.add_argument('--input', default='input/WwiseSound', help='Input WwiseSound directory')
    parser.add_argument('--output', default='out_wwise/txtp_no_gd', help='Output directory for generated txtp files')
    parser.add_argument('--wemdir', default='pool', help='Directory containing carved .wem files')
    args = parser.parse_args()

    wwiser_py = 'tools/wwiser/wwiser.py'
    input_dir = args.input
    out_dir = args.output
    pool_dir = args.wemdir
    os.makedirs(out_dir, exist_ok=True)

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
    render_pool = 'out_wwise/render_pool'
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

    crewvoice_langs = {
        "arb", "en", "ru", "vi", "gup", "de", "ja", "ko", "cn", "cs",
        "en_gb", "es", "fi", "fr", "it", "pbr", "pl", "sv", "th", "tr", "uk", "English(US)"
    }

    print(f"Running wwiser on {len(bnk_files)} banks individually...")
    for idx, bnk in enumerate(bnk_files, 1):
        rel_path = os.path.relpath(bnk, input_dir)
        parts = rel_path.split(os.sep)
        
        lang = None
        if len(parts) > 1 and parts[0] in crewvoice_langs:
            lang = parts[0]
            
        cmd = [
            'python3', wwiser_py,
        ]
        if lang:
            cmd += ['-gl', lang]
        cmd += [
            '-g',  # Generate txtp
            '-go', out_dir,  # Output directory
            '-gw', os.path.abspath(render_pool)  # Directory containing consolidated carved media and banks
        ]
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
                    if lang in crewvoice_langs:
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

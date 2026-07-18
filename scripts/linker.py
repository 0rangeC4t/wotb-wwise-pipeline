import os
import json
import re

def parse_txtp_files(directory):
    """
    Parses any .txtp files exported by wwiser to extract mappings from source ID to friendly paths.
    """
    mappings = {}
    if not os.path.exists(directory):
        return mappings
        
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.txtp'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', errors='ignore') as f:
                        content = f.read()
                    wem_ids = re.findall(r'(\d+)\.wem', content)
                    for wem_id in wem_ids:
                        if wem_id not in mappings:
                            mappings[wem_id] = {
                                "friendly_name": file[:-5], # strip .txtp
                                "object_path": path
                            }
                except Exception:
                    pass
    return mappings

import argparse

def link_manifest():
    parser = argparse.ArgumentParser(description="Link soundbank info, txtp files, and carved pool to generate a manifest and identify orphans.")
    parser.add_argument('--input', default='input/WwiseSound', help='Input WwiseSound directory containing SoundbanksInfo.json')
    parser.add_argument('--output', default='pool', help='Output pool directory containing carved .wem files')
    parser.add_argument('--manifest', default='manifest.json', help='Path to output manifest.json')
    parser.add_argument('--dryrun-log', default='logs/report_dryrun.log', help='Path to output report_dryrun.log')
    parser.add_argument('--txtp-dir', default='out_wwise', help='Directory containing generated txtp routing files')
    args = parser.parse_args()
    
    soundbanks_info_path = os.path.join(args.input, 'SoundbanksInfo.json')
    manifest_path = args.manifest
    dryrun_log_path = args.dryrun_log
    pool_dir = args.output
    txtp_dir = args.txtp_dir
    
    # Ensure all output directories exist
    if os.path.dirname(manifest_path):
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    if os.path.dirname(dryrun_log_path):
        os.makedirs(os.path.dirname(dryrun_log_path), exist_ok=True)
    
    if not os.path.exists(soundbanks_info_path):
        print(f"Error: {soundbanks_info_path} not found.")
        return
        
    with open(soundbanks_info_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    manifest = {}
    
    # 1. Parse StreamedFiles
    streamed_files = data.get("SoundBanksInfo", {}).get("StreamedFiles", [])
    for sf in streamed_files:
        sf_id = sf.get("Id")
        short_name = sf.get("ShortName")
        lang = sf.get("Language")
        if lang == "SFX":
            lang = None
            
        manifest[sf_id] = {
            "friendly_name": os.path.basename(short_name) if short_name else None,
            "object_path": short_name if short_name else None,
            "language": lang
        }
        
    # 2. Parse SoundBanks (embedded files in DIDX, including nested IncludedEvents -> IncludedMemoryFiles)
    soundbanks = data.get("SoundBanksInfo", {}).get("SoundBanks", [])
    for sb in soundbanks:
        lang = sb.get("Language")
        if lang == "SFX":
            lang = None
            
        # Top-level memory files
        included_files = sb.get("IncludedMemoryFiles", [])
        for imf in included_files:
            imf_id = imf.get("Id")
            short_name = imf.get("ShortName")
            
            manifest[imf_id] = {
                "friendly_name": os.path.basename(short_name) if short_name else None,
                "object_path": short_name if short_name else None,
                "language": lang
            }
            
        # Nested event-level memory files (for Voice/Languages)
        included_events = sb.get("IncludedEvents", [])
        for event in included_events:
            event_files = event.get("IncludedMemoryFiles", [])
            for emf in event_files:
                emf_id = emf.get("Id")
                short_name = emf.get("ShortName")
                
                manifest[emf_id] = {
                    "friendly_name": os.path.basename(short_name) if short_name else None,
                    "object_path": short_name if short_name else None,
                    "language": lang
                }
            
    # Enrich with txtp mappings if available (does not affect orphan generation)
    txtp_mappings = parse_txtp_files(txtp_dir)
    for source_id, txtp in txtp_mappings.items():
        if source_id in manifest:
            if not manifest[source_id]["friendly_name"]:
                manifest[source_id]["friendly_name"] = txtp["friendly_name"]
            if not manifest[source_id]["object_path"]:
                manifest[source_id]["object_path"] = txtp["object_path"]
                
    # 3. Scan pool/ directory to get all actually carved IDs
    carved_ids = set()
    if os.path.exists(pool_dir):
        for f in os.listdir(pool_dir):
            if f.endswith('.wem'):
                carved_ids.add(f.split('.')[0])
                
    # 4. Compare to define orphans (actually carved but not in SoundbanksInfo)
    orphans = carved_ids - set(manifest.keys())
    
    # Print the three requested counts
    print(f"Carved IDs count: {len(carved_ids)}")
    print(f"Manifest IDs count: {len(manifest)}")
    print(f"Orphans count: {len(orphans)}")
    
    # 5. Write true orphans to dryrun report
    with open(dryrun_log_path, 'w', encoding='utf-8') as lf:
        if orphans:
            lf.write(f"Orphaned IDs (carved but missing in SoundbanksInfo.json):\n")
            for o in sorted(list(orphans)):
                lf.write(f"{o}\n")
        else:
            lf.write("No orphaned IDs found.\n")
            
    # Write manifest.json
    with open(manifest_path, 'w', encoding='utf-8') as mf:
        json.dump(manifest, mf, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    link_manifest()

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../core'))

from index_parser import parse_akpk, parse_didx
from carve_core import carve_by_index

import argparse
import json

def analyze_duplicate_and_orphans():
    parser = argparse.ArgumentParser(description="Analyze duplicates and orphans with precise JSON parser.")
    parser.add_argument('--input', default='input/WwiseSound', help='Input WwiseSound directory')
    parser.add_argument('--output', default='pool', help='Output pool directory')
    parser.add_argument('--manifest', default='manifest.json', help='Manifest JSON path')
    args = parser.parse_args()

    wwisesound_dir = args.input
    pool_dir = args.output
    manifest_path = args.manifest

    files_to_process = []
    for root, dirs, files in os.walk(wwisesound_dir):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.pck'):
                files_to_process.append((filepath, 'pck'))
            elif file.endswith('.bnk'):
                files_to_process.append((filepath, 'bnk'))
                
    id_sources = {}
    for filepath, ftype in files_to_process:
        try:
            if ftype == 'pck':
                index = parse_akpk(filepath)
            else:
                index = parse_didx(filepath)
            if not index:
                continue
            for entry in index:
                fid = entry['id']
                if fid not in id_sources:
                    id_sources[fid] = []
                id_sources[fid].append({
                    'file': filepath,
                    'size': entry['size']
                })
        except Exception as e:
            pass

    # 1. Print duplicates
    duplicates = {fid: sources for fid, sources in id_sources.items() if len(sources) > 1}
    print(f"Total Unique IDs: {len(id_sources)}")
    print(f"Total Duplicated IDs: {len(duplicates)}")
    print("First 3 Duplicated IDs analysis:")
    for i, (fid, sources) in enumerate(list(duplicates.items())[:3]):
        print(f"Duplicate {i+1} - ID {fid}:")
        for src in sources:
            print(f"  Source file: {src['file']}, Size: {src['size']} bytes")

    # 2. Check 10 orphan IDs
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    pool_ids = set()
    if os.path.exists(pool_dir):
        pool_ids = {f.split('.')[0] for f in os.listdir(pool_dir) if f.endswith('.wem')}
    orphans = sorted(list(pool_ids - set(manifest.keys())))
    print(f"\nTotal Orphans: {len(orphans)}")
    print("First 10 Orphan IDs:")
    print(orphans[:10])
    
    # Precise JSON parsing of SoundbanksInfo.json (no raw string search)
    soundbanks_info_path = os.path.join(wwisesound_dir, 'SoundbanksInfo.json')
    exact_declared_ids = set()
    if os.path.exists(soundbanks_info_path):
        try:
            with open(soundbanks_info_path, 'r', encoding='utf-8') as sf:
                data = json.load(sf)
                
            # StreamedFiles
            for sf_entry in data.get("SoundBanksInfo", {}).get("StreamedFiles", []):
                exact_declared_ids.add(str(sf_entry.get("Id")))
                
            # SoundBanks
            for sb in data.get("SoundBanksInfo", {}).get("SoundBanks", []):
                for imf in sb.get("IncludedMemoryFiles", []):
                    exact_declared_ids.add(str(imf.get("Id")))
                for event in sb.get("IncludedEvents", []):
                    for emf in event.get("IncludedMemoryFiles", []):
                        exact_declared_ids.add(str(emf.get("Id")))
        except Exception as e:
            print(f"Error parsing {soundbanks_info_path}: {e}")
            
    print("\nVerifying first 10 Orphan IDs with exact JSON Id declaration:")
    for oid in orphans[:10]:
        found = oid in exact_declared_ids
        print(f"ID {oid} declared as exact 'Id' in SoundbanksInfo.json? {found}")

if __name__ == '__main__':
    analyze_duplicate_and_orphans()

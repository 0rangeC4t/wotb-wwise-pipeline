import os, re, json, sys, argparse

# Add scripts directory to sys.path so we can import fix_random_container_render
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fix_random_container_render import is_random_container_bug, extract_source_ids

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--wav-dir', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    txtp_dir = 'out_wwise/txtp'
    wav_dir = args.wav_dir
    
    txtp_to_sources = {}
    source_to_txtps = {}
    txtp_to_gamesyncs = {}
    
    state_groups = set()
    switch_groups = set()
    game_parameters = set()
    
    for root, _, files in os.walk(txtp_dir):
        for file in files:
            if file.endswith('.txtp'):
                path = os.path.join(root, file)
                sids = set()
                gamesyncs = []
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.startswith('#'):
                            for m in re.finditer(r'(\d+)\.wem', line):
                                sids.add(m.group(1))
                        else:
                            if 'gamesyncs: [' in line:
                                m = re.search(r'\[(.*?)\]', line)
                                if m:
                                    val = m.group(1)
                                    gamesyncs.append({"type": "switch", "value": val})
                                    switch_groups.add(val.split('=')[0])
                            elif '- ulStateGroupID: (' in line:
                                m = re.search(r'\((.*?)\)', line)
                                if m:
                                    val = m.group(1)
                                    gamesyncs.append({"type": "state", "value": val})
                                    state_groups.add(val.split('=')[0])
                            elif '- RTPCID: {' in line:
                                m = re.search(r'\{(\d+)=', line)
                                if m:
                                    val = m.group(1)
                                    gamesyncs.append({"type": "rtpc", "value": val})
                                    game_parameters.add(val)
                
                txtp_to_sources[path] = sids
                txtp_to_gamesyncs[path] = gamesyncs
                for sid in sids:
                    source_to_txtps.setdefault(sid, set()).add(path)
                    
    # Identify SIDs affected by the Random Container bug (Fact #17)
    affected_sids = set()
    affected_txtps = []
    affected_paths = ['random_bug_files.txt', 'out_wwise/random_container_bug_list_20260802.txt']
    loaded_from_file = False
    for path in affected_paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        affected_txtps.append(parts[1])
            loaded_from_file = True
            break
            
    if not loaded_from_file:
        # Fall back to inline detection logic if list files are not found
        for root, _, files in os.walk(txtp_dir):
            for file in files:
                if file.endswith('.txtp'):
                    fpath = os.path.join(root, file)
                    if is_random_container_bug(fpath):
                        affected_txtps.append(fpath)
                        
    for txtp_path in affected_txtps:
        if os.path.exists(txtp_path):
            sids = extract_source_ids(txtp_path)
            affected_sids.update(sids)

    ambiguous = {}
    valid_mapping = {}
    
    for sid, txtps in source_to_txtps.items():
        is_affected = (sid in affected_sids)
        sid_wav_path = os.path.join(wav_dir, f"{sid}.wav")
        
        if is_affected and os.path.exists(sid_wav_path):
            valid_mapping[sid] = os.path.abspath(sid_wav_path)
            if len(txtps) > 1:
                ambiguous[sid] = sorted(list(txtps))
        else:
            matching_txtps = []
            for txtp_path in sorted(txtps):
                rel = os.path.relpath(txtp_path, txtp_dir)
                wav_path = os.path.join(wav_dir, os.path.splitext(rel)[0] + '.wav')
                if os.path.exists(wav_path):
                    matching_txtps.append((txtp_path, os.path.abspath(wav_path)))
            
            if matching_txtps:
                valid_mapping[sid] = matching_txtps[0][1]
                if len(matching_txtps) > 1:
                    ambiguous[sid] = [p[0] for p in matching_txtps]
                    
    with open(args.manifest, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
        
    path_to_sids = {}
    valid_items = []
    
    for sid, info in manifest.items():
        if info.get('friendly_name') is None:
            continue
        if sid not in valid_mapping:
            continue
            
        lang = info.get('language')
        obj_path_raw = info.get('object_path', '')
        if obj_path_raw.lower().endswith('.wav'):
            obj_path_raw = obj_path_raw[:-4]
            
        obj_path_raw = obj_path_raw.replace('/', '\\')
        final_obj_path = f"\\Actor-Mixer Hierarchy\\Default Work Unit\\{obj_path_raw}"
        
        valid_items.append((sid, info, valid_mapping[sid], final_obj_path))
        path_to_sids.setdefault(final_obj_path, []).append(sid)
        
    import_rows = []
    disambiguation_log = {}
    
    for sid, info, wav_path, base_path in valid_items:
        lang = info.get('language')
        obj_type = "Sound SFX" if lang is None else "Sound Voice"
        
        final_path = base_path
        if len(path_to_sids[base_path]) > 1:
            final_path = f"{base_path}_{sid}"
            log_entry = {"source_id": sid, "new_path": final_path}
            disambiguation_log.setdefault(base_path, []).append(log_entry)
            
        wine_wav_path = "Z:" + wav_path.replace('/', '\\')
        import_rows.append(f"{wine_wav_path}\t{obj_type}\t{final_path}")
        
    with open('disambiguation_log.json', 'w', encoding='utf-8') as f:
        json.dump(disambiguation_log, f, indent=2)
        
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write("Audio File\tObject Type\tObject Path\n")
        f.write("\n".join(import_rows) + "\n")
        
    id_to_gamesync_refs = {}
    for sid in manifest.keys():
        if sid in source_to_txtps:
            gs = []
            for t in source_to_txtps[sid]:
                gs.extend(txtp_to_gamesyncs[t])
            if gs:
                id_to_gamesync_refs[sid] = gs
                
    gamesync_map = {
        "state_groups": list(state_groups),
        "switch_groups": list(switch_groups),
        "game_parameters": list(game_parameters),
        "id_to_gamesync_refs": id_to_gamesync_refs
    }
    
    with open('gamesync_map.json', 'w', encoding='utf-8') as f:
        json.dump(gamesync_map, f, indent=2)
        
    print(f"total source_id -> wav mappings resolved: {len(valid_mapping)}")
    print(f"ambiguous cases count: {len(ambiguous)}")
    print("ambiguous samples:")
    for sid in list(ambiguous.keys())[:5]:
        print(f"  {sid}: {ambiguous[sid]}")
        
    print(f"\nimport.txt row count: {len(import_rows)}")
    print(f"gamesync_map.json summary:")
    print(f"  state_groups: {len(state_groups)}")
    print(f"  switch_groups: {len(switch_groups)}")
    print(f"  game_parameters: {len(game_parameters)}")
    print(f"  id_to_gamesync_refs keys: {len(id_to_gamesync_refs)}")
    
    txtp_with_gs = sum(1 for v in txtp_to_gamesyncs.values() if v)
    txtp_without_gs = len(txtp_to_gamesyncs) - txtp_with_gs
    print(f".txtp files with gamesync data: {txtp_with_gs}")
    print(f".txtp files without gamesync data: {txtp_without_gs}")
    
    print("\ngamesync_map.json sample entries:")
    sample_keys = list(id_to_gamesync_refs.keys())[:5]
    for k in sample_keys:
        print(f"  {k}: {id_to_gamesync_refs[k]}")

if __name__ == '__main__':
    main()

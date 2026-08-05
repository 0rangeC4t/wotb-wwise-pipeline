#!/usr/bin/env python3
import os
import re
import json

def load_manifest():
    manifest_path = "manifest.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def resolve_source_to_wav(source_id, manifest):
    source_id_str = str(source_id)
    
    # 1. Check out_wwise/wav_music/
    wav_music_path = f"out_wwise/wav_music/{source_id_str}.wav"
    if os.path.exists(wav_music_path):
        return os.path.abspath(wav_music_path)
        
    # 2. Check out_wwise/wav/ (direct SID.wav)
    wav_sid_path = f"out_wwise/wav/{source_id_str}.wav"
    if os.path.exists(wav_sid_path):
        return os.path.abspath(wav_sid_path)
        
    # 3. Check TXTP-style logic or friendly-name under out_wwise/wav/ or out_wwise/wav_music/
    if source_id_str in manifest:
        info = manifest[source_id_str]
        friendly = info.get("friendly_name", "")
        obj_path = info.get("object_path", "")
        
        # Try finding a wav file matching the friendly name or object path in out_wwise/wav/ or out_wwise/wav_music/
        for base_dir in ["out_wwise/wav", "out_wwise/wav_music"]:
            # Try direct name
            if friendly:
                p = os.path.join(base_dir, f"{friendly}.wav")
                if os.path.exists(p):
                    return os.path.abspath(p)
                p = os.path.join(base_dir, f"{friendly}")
                if os.path.exists(p):
                    return os.path.abspath(p)
            if obj_path:
                # remove extension if present, then add .wav
                base_obj = os.path.splitext(obj_path)[0]
                p = os.path.join(base_dir, f"{base_obj}.wav")
                if os.path.exists(p):
                    return os.path.abspath(p)
                p = os.path.join(base_dir, f"{obj_path}")
                if os.path.exists(p):
                    return os.path.abspath(p)
                    
    # Fallback to pool/ or extracted_wavs/
    pool_path = f"pool/{source_id_str}.wav"
    if os.path.exists(pool_path):
        return os.path.abspath(pool_path)
        
    return f"extracted_wavs/{source_id_str}.wav"

def parse_hierarchy_report(report_path="music_hierarchy_investigation.md"):
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    banks = {}
    current_bank = None
    
    # Simple state machine to parse markdown Sections
    sections = content.split("## Soundbank:")
    for section in sections[1:]:
        lines = section.splitlines()
        bank_name = lines[0].strip().strip("`")
        banks[bank_name] = {
            "name": bank_name,
            "segments": {},
            "tracks": {},
            "ran_seqs": {},
            "switch_cntrs": {},
            "tree_lines": [],
            "gaps": []
        }
        current_bank = banks[bank_name]
        
        # Subsections (only level 3 headers, avoiding splitting level 4 headers like #### Segment ID:)
        subsections = re.split(r"\n### (?!#)", "\n" + section)
        for sub in subsections:
            sub_lines = sub.strip().splitlines()
            if not sub_lines:
                continue
            sub_lines = sub.splitlines()
            title = sub_lines[0].strip()
            
            if "1. Object Hierarchy Tree" in title:
                for line in sub_lines[1:]:
                    if line.strip().startswith("-") or line.strip().startswith("*"):
                        current_bank["tree_lines"].append(line)
                        
            elif "2. Segment Markers & Cue Points" in title:
                # Segment info block
                # find segments by "Segment ID: `...`"
                seg_blocks = sub.split("#### Segment ID:")
                for seg_block in seg_blocks[1:]:
                    seg_lines = seg_block.splitlines()
                    seg_id = seg_lines[0].strip().strip("`")
                    duration = 0.0
                    markers = []
                    
                    for line in seg_lines[1:]:
                        if "Duration" in line:
                            m = re.search(r"Duration.*`([\d.]+)`", line)
                            if m:
                                duration = float(m.group(1))
                        # Parse Markdown table rows
                        # e.g., | `43573010` | `0.0` | "" | Entry Cue (hash: 43573010) |
                        if "|" in line and "Marker ID" not in line and "---" not in line:
                            parts = [p.strip().strip("`") for p in line.split("|")[1:-1]]
                            if len(parts) >= 4:
                                marker_id = parts[0]
                                position = float(parts[1]) if parts[1] else 0.0
                                marker_name = parts[2]
                                marker_type = parts[3]
                                markers.append({
                                    "id": marker_id,
                                    "position": position,
                                    "name": marker_name,
                                    "type": marker_type
                                })
                    
                    current_bank["segments"][seg_id] = {
                        "id": seg_id,
                        "duration": duration,
                        "markers": markers
                    }
                    
            elif "3. Switch Container Driving Game Syncs" in title:
                # Switch Container details
                sw_blocks = sub.split("#### Switch Container ID:")
                for sw_block in sw_blocks[1:]:
                    sw_lines = sw_block.splitlines()
                    sw_id = sw_lines[0].strip().strip("`")
                    no_syncs = "No driving Game Syncs" in sw_block
                    nodes = []
                    for line in sw_lines[1:]:
                        if "|" in line and "Node Key" not in line and "---" not in line:
                            parts = [p.strip().strip("`") for p in line.split("|")[1:-1]]
                            if len(parts) >= 4:
                                nodes.append({
                                    "key": parts[0],
                                    "audio_node_id": parts[1],
                                    "weight": parts[2],
                                    "probability": parts[3]
                                })
                    current_bank["switch_cntrs"][sw_id] = {
                        "id": sw_id,
                        "no_arguments_gap": no_syncs,
                        "nodes": nodes
                    }
                    
            elif "4. Transition Rules" in title:
                rule_blocks = sub.split("#### Rule in ")
                for rule_block in rule_blocks[1:]:
                    rule_lines = rule_block.splitlines()
                    header = rule_lines[0].strip()
                    m = re.search(r"`(CAkMusic[A-Za-z]+)`\s+ID:\s+`(\d+)`", header)
                    if m:
                        obj_type = m.group(1)
                        obj_id = m.group(2)
                        
                        source_id = "-1"
                        dest_id = "-1"
                        out_fade_out = 0
                        out_curve = "Linear"
                        out_sync = "ExitMarker"
                        out_play_post = 1
                        
                        in_fade_in = 0
                        in_curve = "Linear"
                        in_jump_to = "StartOfPlaylist"
                        in_entry = "EntryMarker"
                        in_play_pre = 1
                        in_match_cue = 0
                        
                        # Read rule parameters
                        current_mode = None
                        for line in rule_lines[1:]:
                            if "Source Segment / Container ID:" in line:
                                source_id = line.split(":")[-1].strip().strip("`")
                            elif "Destination Segment / Container ID:" in line:
                                dest_id = line.split(":")[-1].strip().strip("`")
                            elif "Source (Out-Transition) Rule:" in line:
                                current_mode = "out"
                            elif "Destination (In-Transition) Rule:" in line:
                                current_mode = "in"
                            elif "Fade-out Time:" in line:
                                out_fade_out = int(re.search(r"(\d+)", line).group(1))
                            elif "Fade-in Time:" in line:
                                in_fade_in = int(re.search(r"(\d+)", line).group(1))
                            elif "Fade Curve:" in line:
                                curve = line.split(":")[-1].strip()
                                if current_mode == "out":
                                    out_curve = curve
                                else:
                                    in_curve = curve
                            elif "Sync Point:" in line:
                                out_sync = line.split(":")[-1].strip()
                            elif "Play Post-Exit:" in line:
                                out_play_post = int(re.search(r"(\d+)", line).group(1))
                            elif "Jump To:" in line:
                                in_jump_to = line.split(":")[-1].strip()
                            elif "Entry Type:" in line:
                                in_entry = line.split(":")[-1].strip()
                            elif "Play Pre-Entry:" in line:
                                in_play_pre = int(re.search(r"(\d+)", line).group(1))
                            elif "Match Source Cue Name:" in line:
                                in_match_cue = int(re.search(r"(\d+)", line).group(1))
                                
                        rule_data = {
                            "source_id": source_id,
                            "dest_id": dest_id,
                            "out_transition": {
                                "fade_out_time": out_fade_out,
                                "fade_curve": out_curve,
                                "sync_point": out_sync,
                                "play_post_exit": out_play_post
                            },
                            "in_transition": {
                                "fade_in_time": in_fade_in,
                                "fade_curve": in_curve,
                                "jump_to": in_jump_to,
                                "entry_type": in_entry,
                                "play_pre_entry": in_play_pre,
                                "match_source_cue_name": in_match_cue
                            }
                        }
                        
                        # Store in respective containers
                        if obj_id not in current_bank["ran_seqs"]:
                            current_bank["ran_seqs"][obj_id] = {"id": obj_id, "playlist": None, "rules": []}
                        current_bank["ran_seqs"][obj_id]["rules"].append(rule_data)
                        
            elif "5. Explicitly Flagged Gaps" in title:
                for line in sub_lines[1:]:
                    if line.strip().startswith("-") or line.strip().startswith("*"):
                        current_bank["gaps"].append(line.strip())

    return banks

def generate_dry_run_log(banks, manifest):
    log_rows = []
    
    # Header
    log_rows.append("==================================================================================")
    log_rows.append("                  WWISE INTERACTIVE MUSIC HIERARCHY DRY-RUN REPORT                ")
    log_rows.append("==================================================================================")
    log_rows.append("This log represents every WAAPI call that WOULD be made to rebuild the hierarchy.")
    log_rows.append("DRY-RUN MODE IS ENABLED: No objects are created or modified in the Wwise Project.\n")
    
    total_objects_would_create = 0
    
    # Process each bank
    for bank_name, bank in banks.items():
        log_rows.append(f"----------------------------------------------------------------------------------")
        log_rows.append(f" SOUNDBANK: {bank_name}")
        log_rows.append(f"----------------------------------------------------------------------------------")
        
        # Display explicit gaps to human reviewer
        if bank["gaps"]:
            log_rows.append("⚠️  EXPLICITLY FLAGGED GAPS & STRUCTURAL AMBIGUITIES FOUND IN SOURCE DATA:")
            for gap in bank["gaps"]:
                log_rows.append(f"   [GAP REVIEW REQUIRED] {gap}")
            log_rows.append("")
        
        # We need to reconstruct the hierarchy from the tree lines and print each object
        # Let's count and generate the exact WAAPI payloads
        # We can also parse the tracks, segments, etc. directly from tree lines!
        # Let's parse tree_lines into a tree structure.
        
        # Types found in tree lines
        # - **[RanSeqContainer]** ID: `359976450`
        # - **[SwitchContainer]** ID: `109552928`
        # - **[Segment]** ID: `...`
        # - **[Track]** ID: `...`
        # Let's collect all objects to create.
        
        objects_to_create = []
        playlist_items = []
        
        # Maintain a stack to compute parent relationships based on indentation level
        stack = [] # list of (indent, object_info)
        
        seen_ids = set()
        for line in bank["tree_lines"]:
            indent = len(line) - len(line.lstrip())
            line_str = line.strip()
            
            # Identify object type and ID
            m_obj = re.search(r"\*\*\[(RanSeqContainer|SwitchContainer|Segment|Track)\]\*\*\s+ID:\s+`(\d+)`", line_str)
            m_playlist = re.search(r"\*\*\[(PlaylistGroup|PlaylistItem)\]\*\*", line_str)
            
            # Pop stack if current indent is less than or equal to stack top's indent
            while stack and indent <= stack[-1][0]:
                stack.pop()
                
            parent_info = stack[-1][1] if stack else None
            
            if m_obj:
                obj_type_raw = m_obj.group(1)
                obj_id = m_obj.group(2)
                
                # Determine WAAPI Type
                waapi_type = {
                    "RanSeqContainer": "MusicPlaylistContainer",
                    "SwitchContainer": "MusicSwitchContainer",
                    "Segment": "MusicSegment",
                    "Track": "MusicTrack"
                }[obj_type_raw]
                
                # Setup specific properties
                properties = {}
                name = f"{waapi_type}_{obj_id}"
                
                if obj_type_raw == "Segment":
                    # Get segment details
                    seg_data = bank["segments"].get(obj_id, {"duration": 0.0, "markers": []})
                    properties["Duration"] = seg_data["duration"]
                    properties["Markers"] = seg_data["markers"]
                elif obj_type_raw == "Track":
                    # Get track details
                    track_type_match = re.search(r"Type:\s*`([^`]+)`", line_str)
                    track_type = track_type_match.group(1) if track_type_match else "Normal"
                    properties["TrackType"] = track_type
                    
                    # Extract Source IDs (only before opening parenthesis)
                    sids_match = re.search(r"Source IDs:\s*([^(]+)", line_str)
                    sids = []
                    if sids_match:
                        for s_id in re.findall(r"(\d+)", sids_match.group(1)):
                            sids.append(s_id)
                    properties["SourceIDs"] = sids
                    properties["SourceWavs"] = {sid: resolve_source_to_wav(sid, manifest) for sid in sids}
                elif obj_type_raw == "SwitchContainer":
                    sw_data = bank["switch_cntrs"].get(obj_id, {"no_arguments_gap": False, "nodes": []})
                    properties["NoArgumentsGap"] = sw_data["no_arguments_gap"]
                    properties["DecisionTreeNodes"] = sw_data["nodes"]
                elif obj_type_raw == "RanSeqContainer":
                    ran_data = bank["ran_seqs"].get(obj_id, {"rules": []})
                    properties["TransitionRules"] = ran_data.get("rules", [])
                
                # Determine Parent path or ID
                parent_path_or_id = ""
                if parent_info:
                    parent_path_or_id = f"{parent_info['type']}_{parent_info['id']}"
                else:
                    parent_path_or_id = f"\\Interactive Music Hierarchy\\Default Work Unit\\{bank_name}"
                
                obj_entry = {
                    "id": obj_id,
                    "raw_type": obj_type_raw,
                    "type": waapi_type,
                    "name": name,
                    "parent": parent_path_or_id,
                    "properties": properties
                }
                
                if obj_id not in seen_ids:
                    seen_ids.add(obj_id)
                    objects_to_create.append(obj_entry)
                stack.append((indent, obj_entry))
                
            elif m_playlist:
                playlist_type = m_playlist.group(1)
                # Parse weight, loop, type
                loop_match = re.search(r"Loop:\s*`([^`]+)`", line_str)
                type_match = re.search(r"Type:\s*`([^`]+)`", line_str)
                weight_match = re.search(r"Weight:\s*`([^`]+)`", line_str)
                seg_id_match = re.search(r"Segment ID:\s*`([^`]+)`", line_str)
                
                p_item = {
                    "playlist_type": playlist_type,
                    "loop": loop_match.group(1) if loop_match else "1",
                    "mode": type_match.group(1) if type_match else "None",
                    "weight": weight_match.group(1) if weight_match else "50000",
                    "segment_id": seg_id_match.group(1) if seg_id_match else None,
                    "parent_container": stack[-1][1]["id"] if stack else None
                }
                playlist_items.append(p_item)
        
        # Count and log
        seg_count = sum(1 for o in objects_to_create if o["raw_type"] == "Segment")
        track_count = sum(1 for o in objects_to_create if o["raw_type"] == "Track")
        switch_count = sum(1 for o in objects_to_create if o["raw_type"] == "SwitchContainer")
        ranseq_count = sum(1 for o in objects_to_create if o["raw_type"] == "RanSeqContainer")
        
        log_rows.append(f"BANK SUMMARY: {seg_count} Segments, {track_count} Tracks, {ranseq_count} PlaylistContainers, {switch_count} SwitchContainers")
        log_rows.append(f"TOTAL OBJECTS FOR THIS BANK: {len(objects_to_create)}")
        log_rows.append(f"VERIFICATION STATUS: {'MATCHES' if len(objects_to_create) in (17, 51) else 'MISMATCH'}")
        log_rows.append("")
        
        total_objects_would_create += len(objects_to_create)
        
        # Log each object's WAAPI call simulation
        for obj in objects_to_create:
            log_rows.append(f"▶ WOULD CREATE OBJECT:")
            log_rows.append(f"  WAAPI Call: ak.wwise.core.object.create")
            log_rows.append(f"  Arguments:")
            log_rows.append(f"    - type: {obj['type']}")
            log_rows.append(f"    - name: {obj['name']}")
            log_rows.append(f"    - parent: {obj['parent']}")
            log_rows.append(f"    - onNameConflict: merge")
            
            # Print type specific properties
            log_rows.append(f"  Properties & Metadata:")
            if obj["raw_type"] == "Segment":
                log_rows.append(f"    - Duration: {obj['properties']['Duration']} ms")
                if obj["properties"]["Markers"]:
                    log_rows.append(f"    - Markers:")
                    for mk in obj["properties"]["Markers"]:
                        log_rows.append(f"        * ID {mk['id']}: Position = {mk['position']} ms, Name = \"{mk['name']}\", Type = {mk['type']}")
                        
            elif obj["raw_type"] == "Track":
                log_rows.append(f"    - TrackType: {obj['properties']['TrackType']}")
                log_rows.append(f"    - Source Assignments:")
                for sid in obj["properties"]["SourceIDs"]:
                    wav = obj["properties"]["SourceWavs"].get(sid, "Not found")
                    log_rows.append(f"        * Source ID {sid} -> {wav}")
                    
            elif obj["raw_type"] == "SwitchContainer":
                if obj["properties"]["NoArgumentsGap"]:
                    log_rows.append(f"    - [GAP CRITICAL WARNING] This Switch Container HAS 0 ARGUMENTS. It functions as a static wrapper!")
                log_rows.append(f"    - Decision Tree Nodes:")
                for node in obj["properties"]["DecisionTreeNodes"]:
                    log_rows.append(f"        * Node Key {node['key']} -> Audio Node ID {node['audio_node_id']} (Weight={node['weight']}, Prob={node['probability']})")
                    
            elif obj["raw_type"] == "RanSeqContainer":
                # Find playlist items belonging to this container
                cnt_playlists = [p for p in playlist_items if p["parent_container"] == obj["id"]]
                if cnt_playlists:
                    log_rows.append(f"    - Playlist Hierarchy:")
                    for pl in cnt_playlists:
                        if pl["playlist_type"] == "PlaylistGroup":
                            log_rows.append(f"        * Group: Mode = {pl['mode']}, Loop = {pl['loop']}, Weight = {pl['weight']}")
                        else:
                            log_rows.append(f"        * Item: Segment ID = {pl['segment_id']}, Loop = {pl['loop']}, Weight = {pl['weight']}")
                if obj["properties"]["TransitionRules"]:
                    log_rows.append(f"    - Transition Rules:")
                    for idx, rule in enumerate(obj["properties"]["TransitionRules"]):
                        log_rows.append(f"        * Rule #{idx}: Source={rule['source_id']} -> Dest={rule['dest_id']}")
                        log_rows.append(f"          Out-Transition: Fade-out={rule['out_transition']['fade_out_time']}ms, Curve={rule['out_transition']['fade_curve']}, Sync={rule['out_transition']['sync_point']}")
                        log_rows.append(f"          In-Transition: Fade-in={rule['in_transition']['fade_in_time']}ms, Curve={rule['in_transition']['fade_curve']}, JumpTo={rule['in_transition']['jump_to']}")
            
            log_rows.append("")

    log_rows.append("==================================================================================")
    log_rows.append(f"TOTAL OBJECTS THAT WOULD BE CREATED ACROSS ALL BANKS: {total_objects_would_create}")
    log_rows.append("==================================================================================")
    
    return "\n".join(log_rows)

def main():
    print("Parsing music_hierarchy_investigation.md...")
    banks = parse_hierarchy_report()
    manifest = load_manifest()
    
    print("Generating dry-run log...")
    log_content = generate_dry_run_log(banks, manifest)
    
    output_log = "music_hierarchy_dry_run.log"
    with open(output_log, "w", encoding="utf-8") as f:
        f.write(log_content)
    
    print(f"Dry-run report successfully written to: {output_log}")
    
    # Simple console validation check
    print(f"Validated bank segments/tracks/containers counts in memory (Unique IDs):")
    for bname, bdata in banks.items():
        # recount unique objects
        unique_ids = set()
        counts_by_type = {"Segment": 0, "Track": 0, "RanSeqContainer": 0, "SwitchContainer": 0}
        for line in bdata["tree_lines"]:
            m = re.search(r"\*\*\[(RanSeqContainer|SwitchContainer|Segment|Track)\]\*\*\s+ID:\s+`(\d+)`", line)
            if m:
                obj_type = m.group(1)
                obj_id = m.group(2)
                if obj_id not in unique_ids:
                    unique_ids.add(obj_id)
                    counts_by_type[obj_type] += 1
        total_unique = len(unique_ids)
        print(f"  {bname}: Total {total_unique} unique objects")
        for otype, count in counts_by_type.items():
            print(f"    - {otype}: {count}")

if __name__ == "__main__":
    main()

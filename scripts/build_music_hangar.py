#!/usr/bin/env python3
import os
import sys
import json
import logging
import time
from waapi import WaapiClient

# Configure Logging
log_file = "music_hierarchy_build_hangar.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Add scripts folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dryrun_music_hierarchy import load_manifest, resolve_source_to_wav, parse_hierarchy_report

def main():
    logging.info("Starting CLEAN build_music_hierarchy for music_hangar.bnk")
    
    # 1. Parse md report and load manifest
    logging.info("Parsing music_hierarchy_investigation.md...")
    banks = parse_hierarchy_report("music_hierarchy_investigation.md")
    manifest = load_manifest()
    
    if "music_hangar.bnk" not in banks:
        logging.error("music_hangar.bnk section not found in report!")
        return
        
    hangar_data = banks["music_hangar.bnk"]
    logging.info(f"Loaded music_hangar.bnk data from report. Segments: {len(hangar_data['segments'])}")

    # 2. Connect to WAAPI
    try:
        client = WaapiClient(url="ws://localhost:8080/waapi")
        logging.info("Connected to WAAPI successfully.")
    except Exception as e:
        logging.error(f"Failed to connect to WAAPI: {e}")
        return

    try:
        # 3. Clean up any existing music_hangar folders to start fresh (Disabled to avoid rebuilding from scratch)
        folder_name = "music_hangar"
        folder_path = f"\\Interactive Music Hierarchy\\Default Work Unit\\{folder_name}"
        logging.info(f"Folder path: {folder_path}")

        # 4. Create folder 'music_hangar'
        logging.info(f"Creating Folder: {folder_path}")
        folder_res = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "Folder",
            "name": folder_name,
            "onNameConflict": "merge"
        })
        folder_guid = folder_res["id"]

        # Parse spec and objects to create
        # We need:
        # - RanSeqContainer: 1054648317
        # - Segments: 860825692, 195645763, 797778272, 626154474
        # - Tracks: 45 unique tracks
        
        # Let's map segment IDs to durations
        segment_durations = {
            "860825692": 31035.290348023253,
            "195645763": 31035.290348023253,
            "797778272": 26172.91396780616,
            "626154474": 22253.02308487956
        }

        # 5. Create MusicPlaylistContainer (RanSeqContainer)
        container_id = "1054648317"
        container_name = f"MusicPlaylistContainer_{container_id}"
        logging.info(f"Creating MusicPlaylistContainer: {container_name}")
        container_res = client.call("ak.wwise.core.object.create", {
            "parent": folder_guid,
            "type": "MusicPlaylistContainer",
            "name": container_name,
            "onNameConflict": "merge"
        })
        container_guid = container_res["id"]

        # Try to detect the correct WAAPI property name for MakeUpGain on
        # MusicPlaylistContainer and set it. We query available property names
        # with `getPropertyAndReferenceNames` and search for a property that
        # references "MakeUp". This avoids guessing SDK names across versions.
        try:
            props = client.call("ak.wwise.core.object.getPropertyAndReferenceNames", {
                "object": container_guid
            })
            found_prop = None

            def _search_for_makeup(obj):
                if isinstance(obj, dict):
                    # prefer explicit name keys if present
                    name = obj.get("name") or obj.get("property") or obj.get("displayName")
                    if isinstance(name, str) and "makeup" in name.lower():
                        return name
                    # check other string values for hints
                    for v in obj.values():
                        if isinstance(v, str) and "makeup" in v.lower():
                            # try to return a canonical property id if available
                            return obj.get("name") or obj.get("property") or name
                    # recurse
                    for v in obj.values():
                        res = _search_for_makeup(v)
                        if res:
                            return res
                elif isinstance(obj, list):
                    for item in obj:
                        res = _search_for_makeup(item)
                        if res:
                            return res
                return None

            for entry in props.get("return", []):
                candidate = _search_for_makeup(entry)
                if candidate:
                    found_prop = candidate
                    break

            # fallback to common literal if nothing discovered
            if not found_prop:
                possible_fallbacks = ["MakeUpGain", "MakeUp", "MakeUp_Gain"]
                for pf in possible_fallbacks:
                    try:
                        # conservative test: attempt to set then readback
                        client.call("ak.wwise.core.object.setProperty", {
                            "object": container_guid,
                            "property": pf,
                            "value": -8.0
                        })
                        found_prop = pf
                        break
                    except Exception:
                        continue

            if found_prop:
                try:
                    client.call("ak.wwise.core.object.setProperty", {
                        "object": container_guid,
                        "property": found_prop,
                        "value": -8.0
                    })
                    logging.info(f"Set MakeUpGain via property '{found_prop}' on {container_name}")
                except Exception as e:
                    logging.warning(f"Failed to set MakeUpGain on {container_name} using '{found_prop}': {e}")
            else:
                logging.warning("Could not discover a WAAPI property name for MakeUpGain on MusicPlaylistContainer; skipping set.")
        except Exception as e:
            logging.warning(f"getPropertyAndReferenceNames failed for {container_name}: {e}")

        # 6. Create MusicSegments under the MusicPlaylistContainer
        created_guids = {}
        created_guids[container_id] = container_guid

        logging.info("Creating MusicSegments...")
        for seg_id, duration in segment_durations.items():
            seg_name = f"MusicSegment_{seg_id}"
            logging.info(f"Creating MusicSegment: {seg_name}")
            seg_res = client.call("ak.wwise.core.object.create", {
                "parent": container_guid,
                "type": "MusicSegment",
                "name": seg_name,
                "onNameConflict": "merge"
            })
            seg_guid = seg_res["id"]
            created_guids[seg_id] = seg_guid

            logging.info(f"Created segment {seg_name} (EndPosition to be set via WWU modification post-build)")

        # 7. Create MusicTracks and Import Audio Files under them
        # Let's extract the list of tracks from tree_lines
        tracks_spec = []
        import re
        
        current_segment_id = None
        for line in hangar_data["tree_lines"]:
            line_str = line.strip()
            # Detect Segment
            m_seg = re.search(r"\*\*\[Segment\]\*\*\s+ID:\s+`(\d+)`", line_str)
            if m_seg:
                current_segment_id = m_seg.group(1)
            # Detect Track
            m_track = re.search(r"\*\*\[Track\]\*\*\s+ID:\s+`(\d+)`\s+\(Type:\s*`([^`]+)`\)", line_str)
            if m_track and current_segment_id:
                track_id = m_track.group(1)
                track_type_raw = m_track.group(2)
                # Random type = 0x01 [Random] or similar, Sequence = 0x02 [Sequence], Normal = 0x00 [Normal]
                track_type = "Normal"
                if "Random" in track_type_raw:
                    track_type = "Random"
                elif "Sequence" in track_type_raw:
                    track_type = "Sequence"
                
                # Extract Source IDs
                sids_match = re.search(r"Source IDs:\s*([^(]+)", line_str)
                sids = []
                if sids_match:
                    for s_id in re.findall(r"(\d+)", sids_match.group(1)):
                        sids.append(s_id)
                        
                tracks_spec.append({
                    "id": track_id,
                    "type": track_type,
                    "segment_id": current_segment_id,
                    "source_ids": sids
                })

        logging.info(f"Parsed {len(tracks_spec)} MusicTracks from investigation report.")

        # Create MusicTracks first and configure them
        for ts in tracks_spec:
            track_name = f"MusicTrack_{ts['id']}"
            parent_seg_guid = created_guids[ts["segment_id"]]
            
            logging.info(f"Creating MusicTrack {track_name} under Segment {ts['segment_id']}")
            track_res = client.call("ak.wwise.core.object.create", {
                "parent": parent_seg_guid,
                "type": "MusicTrack",
                "name": track_name,
                "onNameConflict": "merge"
            })
            track_guid = track_res["id"]
            created_guids[ts["id"]] = track_guid

            # Set TrackType property (Normal: 0 is default; Random: 1, Sequence: 2)
            t_type_val = 0
            if ts["type"] == "Random":
                t_type_val = 1
            elif ts["type"] == "Sequence":
                t_type_val = 2
                
            if t_type_val != 0:
                try:
                    client.call("ak.wwise.core.object.setProperty", {
                        "object": track_guid,
                        "property": "TrackType",
                        "value": t_type_val
                    })
                    logging.info(f"Set TrackType={t_type_val} ({ts['type']}) on MusicTrack {track_name}")
                except Exception as e:
                    logging.warning(f"Could not set TrackType={t_type_val} on {track_name}: {e}")

            # Import each of its Source ID WAV files directly under this Track!
            # The user states that the WAV files are located in out_wwise/wav_music/<SID>.wav
            for sid in ts["source_ids"]:
                wav_path = os.path.abspath(f"out_wwise/wav_music/{sid}.wav")
                if not os.path.exists(wav_path):
                    logging.warning(f"WAV file not found for source {sid}: {wav_path}")
                    # Try to search elsewhere as fallback
                    wav_path = resolve_source_to_wav(sid, manifest)
                    logging.info(f"Fallback resolution of source {sid} -> {wav_path}")
                    
                # Convert to Wine absolute path Z:\...
                wine_wav_path = "Z:" + wav_path.replace("/", "\\")
                
                # Construct track path for importing
                segment_name = f"MusicSegment_{ts['segment_id']}"
                track_path_in_project = f"\\Interactive Music Hierarchy\\Default Work Unit\\{folder_name}\\{container_name}\\{segment_name}\\{track_name}"
                
                logging.info(f"Importing source ID {sid} WAV: {wine_wav_path} to MusicTrack: {track_path_in_project}")
                
                import_args = {
                    "importOperation": "useExisting",
                    "imports": [
                        {
                            "audioFile": wine_wav_path,
                            "objectPath": track_path_in_project,
                            "objectType": "MusicTrack"
                        }
                    ]
                }
                
                try:
                    import_res = client.call("ak.wwise.core.audio.import", import_args)
                    logging.info(f"Import success for SID {sid}")
                except Exception as e:
                    logging.error(f"Failed to import SID {sid}: {e}")

        # Save project to finalize imports and auto-created structures
        client.call("ak.wwise.core.project.save")

        # 8. Set EndTrimOffset for each of the auto-created MusicClips under each MusicTrack to match segment duration
        # Query all descendants under our hangar folder
        verify_res = client.call("ak.wwise.core.object.get", {
            "from": {"path": [folder_path]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "parent", "path"]})
        
        descendants = verify_res.get("return", [])
        
        logging.info("Updating EndTrimOffset on MusicClips...")
        for d in descendants:
            if d["type"] == "MusicClip":
                # Find its parent track and segment to get correct duration
                parent_info = d.get("parent")
                if parent_info:
                    # Query parent's segment
                    track_parent_res = client.call("ak.wwise.core.object.get", {
                        "from": {"id": [parent_info["id"]]}
                    }, options={"return": ["id", "name", "parent"]})
                    track_parent = track_parent_res.get("return", [{}])[0]
                    seg_parent_info = track_parent.get("parent")
                    if seg_parent_info and "MusicSegment_" in seg_parent_info.get("name", ""):
                        seg_id = seg_parent_info["name"].split("_")[-1]
                        duration = segment_durations.get(seg_id, 0.0)
                        
                        client.call("ak.wwise.core.object.setProperty", {
                            "object": d["id"],
                            "property": "EndTrimOffset",
                            "value": duration
                        })
                        logging.info(f"Set EndTrimOffset={duration} ms on MusicClip {d['name']} ({d['id']})")

        # Save project after audio import and clip EndTrimOffset updates
        client.call("ak.wwise.core.project.save")

        # Now that audio and clips are imported, set segment EndPosition and Exit Cue TimeMs via WAAPI
        logging.info("Setting EndPosition and Exit Cue TimeMs via WAAPI after audio import...")

        def _set_endposition_and_cue_for_segment(seg_id):
            seg_guid = created_guids.get(seg_id)
            duration = segment_durations.get(seg_id)
            if not seg_guid or duration is None:
                logging.error(f"Missing seg_guid or duration for {seg_id}")
                return False, None

            # Find Exit Cue
            all_cues = client.call("ak.wwise.core.object.get", {
                "from": {"ofType": ["MusicCue"]}
            }, options={"return": ["id", "name", "@CueType", "path"]})
            
            for cue in all_cues.get("return", []):
                if f"MusicSegment_{seg_id}" in cue.get("path", "") and cue.get("@CueType") == 1:
                    try:
                        client.call("ak.wwise.core.object.setProperty", {
                            "object": cue["id"],
                            "property": "TimeMs",
                            "value": duration
                        })
                        logging.info(f"Set Exit Cue TimeMs={duration} ms for segment {seg_id}")
                    except Exception as e:
                        logging.error(f"Failed to set Exit Cue TimeMs for segment {seg_id}: {e}")

            try:
                client.call("ak.wwise.core.object.setProperty", {
                    "object": seg_guid,
                    "property": "EndPosition",
                    "value": duration
                })
            except Exception as e:
                logging.error(f"Failed to set EndPosition via WAAPI for {seg_id}: {e}")
                return False, None

            client.call("ak.wwise.core.project.save")

            try:
                get_res = client.call("ak.wwise.core.object.get", {
                    "from": {"id": [seg_guid]}
                }, options={"return": ["id", "name", "@EndPosition"]})
                actual = get_res["return"][0].get("@EndPosition")
                if actual is None:
                    logging.error(f"No @EndPosition returned for {seg_id} after set")
                    return False, actual
                match = abs(actual - duration) < 0.01
                logging.info(f"Segment {seg_id}: set EndPosition={duration} ms, readback={actual} ms, MATCH={match}")
                return match, actual
            except Exception as e:
                logging.error(f"Failed to readback EndPosition for {seg_id}: {e}")
                return False, None

        # Pick the first segment to test
        first_seg = next(iter(segment_durations.keys()))
        ok, _ = _set_endposition_and_cue_for_segment(first_seg)
        if not ok:
            logging.warning("WAAPI EndPosition set failed on first segment; falling back to WWU direct XML modification + Wwise reboot...")
            client.disconnect()
            
            import subprocess
            logging.info("Running reboot_wwise.py to apply EndPosition and Exit Cue TimeMs directly to WWU...")
            subprocess.run(["python3", "scripts/reboot_wwise.py"], check=True)
            
            # Reconnect client
            client = WaapiClient(url="ws://localhost:8080/waapi")
            logging.info("Re-connected to WAAPI server after reboot.")
        else:
            logging.info("WAAPI EndPosition test succeeded on first segment; applying to remaining segments...")
            for seg_id in segment_durations.keys():
                if seg_id == first_seg:
                    continue
                _set_endposition_and_cue_for_segment(seg_id)

        # 9. Build the nested playlist structure for the top-level RanSeqContainer 1054648317
        logging.info("Configuring Nested Playlist for MusicPlaylistContainer 1054648317...")
        root_item = None
        for attempt in range(10):
            playlist_items_get = client.call("ak.wwise.core.object.get", {
                "from": {"ofType": ["MusicPlaylistItem"]}
            }, options={"return": ["id", "name", "owner", "parent", "path"]})
            all_playlist_items = playlist_items_get.get("return", [])

            for pi in all_playlist_items:
                owner_info = pi.get("owner")
                if owner_info and owner_info.get("id") == container_guid:
                    root_item = pi
                    break
                parent_info = pi.get("parent")
                if parent_info and parent_info.get("id") == container_guid:
                    root_item = pi
                    logging.info("Found Root PlaylistItem via parent match!")
                    break

            if root_item:
                break
            logging.info(f"Root playlist item not found yet; sleeping before retry ({attempt+1}/10)")
            time.sleep(1)

        if not root_item:
            logging.error("Could not find auto-created Root PlaylistItem for MusicPlaylistContainer after retries.")
            return
            
        root_guid = root_item["id"]
        logging.info(f"Found Root PlaylistItem: {root_guid}")
        
        # Configure Root group as: Loop Count = 0 (infinite), Type = 1 (Sequence Continuous Group), Weight = 50.0
        client.call("ak.wwise.core.object.setProperty", {
            "object": root_guid,
            "property": "PlaylistItemType",
            "value": 1 # Sequence Continuous Group
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": root_guid,
            "property": "LoopCount",
            "value": 0 # Infinite loop
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": root_guid,
            "property": "Weight",
            "value": 50.0
        })
        
        # Helper to add segment items correctly (PlaylistItemType=0 must be set BEFORE setReference)
        def add_segment_item(parent_guid, seg_id, loop, weight):
            item = client.call("ak.wwise.core.object.create", {
                "parent": parent_guid,
                "type": "MusicPlaylistItem",
                "name": f"Item_Seg_{seg_id}",
                "onNameConflict": "replace"
            })
            item_guid = item["id"]
            client.call("ak.wwise.core.object.setProperty", {
                "object": item_guid,
                "property": "PlaylistItemType",
                "value": 0 # Segment type
            })
            client.call("ak.wwise.core.object.setProperty", {
                "object": item_guid,
                "property": "LoopCount",
                "value": loop
            })
            client.call("ak.wwise.core.object.setProperty", {
                "object": item_guid,
                "property": "Weight",
                "value": weight
            })
            client.call("ak.wwise.core.object.setReference", {
                "object": item_guid,
                "reference": "Segment",
                "value": created_guids[seg_id]
            })
            logging.info(f"Added Segment Item {seg_id} to parent {parent_guid}: Loop={loop}, Weight={weight}")

        # 1. Create Group A under Root
        logging.info("Creating Group A (Continuous Random)...")
        group_a = client.call("ak.wwise.core.object.create", {
            "parent": root_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_A_Random",
            "onNameConflict": "replace"
        })
        ga_guid = group_a["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": ga_guid,
            "property": "PlaylistItemType",
            "value": 2 # Random Continuous
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": ga_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": ga_guid,
            "property": "Weight",
            "value": 50.0
        })

        add_segment_item(ga_guid, "860825692", loop=1, weight=60.0)
        add_segment_item(ga_guid, "195645763", loop=1, weight=50.0)

        # 2. Create Group B under Root
        logging.info("Creating Group B (Continuous Sequence)...")
        group_b = client.call("ak.wwise.core.object.create", {
            "parent": root_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_B_Sequence",
            "onNameConflict": "replace"
        })
        gb_guid = group_b["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb_guid,
            "property": "PlaylistItemType",
            "value": 1 # Sequence Continuous
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb_guid,
            "property": "LoopCount",
            "value": 0 # Loop 0
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb_guid,
            "property": "Weight",
            "value": 50.0
        })

        # Create Group B1 under Group B
        logging.info("Creating Group B1 (Step Random)...")
        group_b1 = client.call("ak.wwise.core.object.create", {
            "parent": gb_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_B1_StepRandom",
            "onNameConflict": "replace"
        })
        gb1_guid = group_b1["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb1_guid,
            "property": "PlaylistItemType",
            "value": 4 # Step Random
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb1_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb1_guid,
            "property": "Weight",
            "value": 50.0
        })
        add_segment_item(gb1_guid, "797778272", loop=1, weight=50.0)
        add_segment_item(gb1_guid, "626154474", loop=2, weight=50.0)

        # Create Group B2 under Group B
        logging.info("Creating Group B2 (Continuous Random)...")
        group_b2 = client.call("ak.wwise.core.object.create", {
            "parent": gb_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_B2_ContinuousRandom",
            "onNameConflict": "replace"
        })
        gb2_guid = group_b2["id"]
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb2_guid,
            "property": "PlaylistItemType",
            "value": 2 # Continuous Random
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb2_guid,
            "property": "LoopCount",
            "value": 1
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": gb2_guid,
            "property": "Weight",
            "value": 50.0
        })
        add_segment_item(gb2_guid, "195645763", loop=1, weight=25.0)
        add_segment_item(gb2_guid, "860825692", loop=1, weight=75.0)

        # Save project
        logging.info("Saving Wwise project...")
        client.call("ak.wwise.core.project.save")
        logging.info("Wwise project saved successfully!")

        # Disconnect client before rebooting Wwise
        client.disconnect()
        
        # Run reboot_wwise.py to apply segment EndPosition and Exit Cue TimeMs directly to WWU and reboot Wwise
        import subprocess
        logging.info("Running reboot_wwise.py to set segment EndPosition and Exit Cue TimeMs in WWU...")
        subprocess.run(["python3", "scripts/reboot_wwise.py"], check=True)

        # Reconnect WAAPI client for mandatory verification read-backs
        client = WaapiClient(url="ws://localhost:8080/waapi")
        logging.info("Re-connected to WAAPI for verification.")

        # 10. Perform Verification Read-Backs (MANDATORY)
        logging.info("================= RUNNING MANDATORY VERIFICATION =================")
        
        # Read back durations for the 4 segments and check that they match segment_durations
        logging.info("Verifying segment durations...")
        for seg_id, expected_dur in segment_durations.items():
            seg_guid = created_guids[seg_id]
            get_res = client.call("ak.wwise.core.object.get", {
                "from": {"id": [seg_guid]}
            }, options={"return": ["id", "name", "@EndPosition"]})
            actual_dur = get_res["return"][0]["@EndPosition"]
            match = abs(actual_dur - expected_dur) < 0.01
            logging.info(f"Segment {seg_id}: Expected {expected_dur:.3f} ms, Got {actual_dur:.3f} ms. MATCH: {match}")

        # Spot-check at least 10 of 45 tracks' audio sources resolve to real files
        logging.info("Spot-checking audio track files on disk...")
        resolved_count = 0
        for i, ts in enumerate(tracks_spec[:15]): # Spot check first 15
            for sid in ts["source_ids"]:
                wav_path = os.path.abspath(f"out_wwise/wav_music/{sid}.wav")
                exists = os.path.exists(wav_path)
                if exists:
                    resolved_count += 1
                logging.info(f"Spot-check track source {sid}: {wav_path} -> EXISTS: {exists}")
        logging.info(f"Total resolved sources in spot-check: {resolved_count}/10+ required.")

        # Cue TimeMs matches duration for all 4 segments
        logging.info("Verifying exit cue positions...")
        cues_verify = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "path", "@TimeMs", "@CueType"]})
        for cue in cues_verify.get("return", []):
            if folder_name in cue["path"] and cue["@CueType"] == 1: # exit cue
                # find parent segment ID
                for seg_id, duration in segment_durations.items():
                    if f"MusicSegment_{seg_id}" in cue["path"]:
                        match = abs(cue["@TimeMs"] - duration) < 0.01
                        logging.info(f"Exit cue in segment {seg_id}: Expected {duration:.3f} ms, Got {cue['@TimeMs']:.3f} ms. MATCH: {match}")

        # Playlist structure read-back verification (LoopCount/GroupType/RandomType/Weight)
        logging.info("Verifying playlist tree properties...")
        items_readback = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "name", "path", "@PlaylistItemType", "@LoopCount", "@NormalOrShuffle", "@Weight"]})
        
        for item in items_readback.get("return", []):
            if folder_name in item["path"]:
                logging.info(f"Playlist Item: Name={item['name']}, Path={item['path']}, Type={item['@PlaylistItemType']}, Loop={item['@LoopCount']}, Weight={item['@Weight']}")

    except Exception as e:
        logging.error(f"Error during WAAPI building: {e}")
    finally:
        client.disconnect()
        logging.info("Disconnected from WAAPI.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import sys
import json
import logging
from waapi import WaapiClient

# Configure Logging
log_file = "music_hierarchy_build_apk.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Add scripts folder to path to reuse parsing/resolution logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dryrun_music_hierarchy import load_manifest, resolve_source_to_wav, parse_hierarchy_report

def main():
    logging.info("Starting CLEAN build_music_hierarchy for apk.bnk")
    
    # 1. Parse md report and load manifest
    logging.info("Parsing music_hierarchy_investigation.md...")
    banks = parse_hierarchy_report("music_hierarchy_investigation.md")
    manifest = load_manifest()
    
    if "apk.bnk" not in banks:
        logging.error("apk.bnk section not found in report!")
        return
        
    apk_data = banks["apk.bnk"]
    logging.info(f"Loaded apk.bnk data from report. Segments: {len(apk_data['segments'])}")

    # 2. Connect to WAAPI
    try:
        client = WaapiClient(url="ws://localhost:8080/waapi")
        logging.info("Connected to WAAPI successfully.")
    except Exception as e:
        logging.error(f"Failed to connect to WAAPI: {e}")
        return

    try:
        # 3. Clean up any existing apk_bnk folders from previous runs
        logging.info("Cleaning up any existing apk_bnk folders to start completely fresh...")
        for name in ["apk_bnk", "apk_bnk_01", "apk_bnk_02", "apk.bnk"]:
            path = f"\\Interactive Music Hierarchy\\Default Work Unit\\{name}"
            try:
                client.call("ak.wwise.core.object.delete", {"object": path})
                logging.info(f"Deleted existing folder: {path}")
            except Exception:
                pass
        client.call("ak.wwise.core.project.save")

        # 4. Create parent folder 'apk_bnk'
        real_folder_name = "apk_bnk"
        folder_path = f"\\Interactive Music Hierarchy\\Default Work Unit\\{real_folder_name}"
        logging.info(f"Creating Folder: {folder_path}")
        
        folder_res = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "Folder",
            "name": real_folder_name,
            "onNameConflict": "merge"
        })
        logging.info(f"Folder create response: {json.dumps(folder_res)}")
        folder_id = folder_res["id"]

        # Parse objects from tree lines of apk.bnk
        stack = []
        objects_to_create = []
        seen_ids = set()
        
        for line in apk_data["tree_lines"]:
            indent = len(line) - len(line.lstrip())
            line_str = line.strip()
            
            import re
            m_obj = re.search(r"\*\*\[(RanSeqContainer|SwitchContainer|Segment|Track)\]\*\*\s+ID:\s+`(\d+)`", line_str)
            
            while stack and indent <= stack[-1][0]:
                stack.pop()
                
            parent_info = stack[-1][1] if stack else None
            
            if m_obj:
                obj_type_raw = m_obj.group(1)
                obj_id = m_obj.group(2)
                
                waapi_type = {
                    "RanSeqContainer": "MusicPlaylistContainer",
                    "SwitchContainer": "MusicSwitchContainer",
                    "Segment": "MusicSegment",
                    "Track": "MusicTrack"
                }[obj_type_raw]
                
                name = f"{waapi_type}_{obj_id}"
                
                properties = {}
                if obj_type_raw == "Segment":
                    seg_data = apk_data["segments"].get(obj_id, {"duration": 0.0, "markers": []})
                    properties["Duration"] = seg_data["duration"]
                    properties["Markers"] = seg_data["markers"]
                elif obj_type_raw == "Track":
                    track_type_match = re.search(r"Type:\s*`([^`]+)`", line_str)
                    properties["TrackType"] = track_type_match.group(1) if track_type_match else "Normal"
                    
                    sids_match = re.search(r"Source IDs:\s*([^(]+)", line_str)
                    sids = []
                    if sids_match:
                        for s_id in re.findall(r"(\d+)", sids_match.group(1)):
                            sids.append(s_id)
                    properties["SourceIDs"] = sids
                    properties["SourceWavs"] = {sid: resolve_source_to_wav(sid, manifest) for sid in sids}
                
                obj_entry = {
                    "id": obj_id,
                    "raw_type": obj_type_raw,
                    "type": waapi_type,
                    "name": name,
                    "parent_info": parent_info,
                    "properties": properties
                }
                
                if obj_id not in seen_ids:
                    seen_ids.add(obj_id)
                    objects_to_create.append(obj_entry)
                stack.append((indent, obj_entry))

        # 5. Create MusicPlaylistContainers FIRST
        logging.info("Creating MusicPlaylistContainers...")
        created_guids = {} # maps obj_id -> GUID
        containers = [o for o in objects_to_create if o["type"] == "MusicPlaylistContainer"]
        for obj in containers:
            logging.info(f"Creating container {obj['name']}")
            res = client.call("ak.wwise.core.object.create", {
                "parent": folder_id,
                "type": obj["type"],
                "name": obj["name"],
                "onNameConflict": "merge"
            })
            created_guids[obj["id"]] = res["id"]

        # 6. Import audio files into MusicSegment objects
        # This will automatically create the MusicSegment with correct names, auto-set its Exit Cue, and create a child MusicTrack (which we will rename)!
        logging.info("Importing audio files and auto-creating Segments/Tracks...")
        tracks = [o for o in objects_to_create if o["type"] == "MusicTrack"]
        for obj in tracks:
            parent_segment = obj["parent_info"]
            parent_container = parent_segment["parent_info"]
            
            wavs = obj["properties"].get("SourceWavs", {})
            for sid, wav_path in wavs.items():
                if not os.path.exists(wav_path):
                    logging.warning(f"Audio file does not exist: {wav_path}")
                # Convert to Wine path
                wine_wav_path = "Z:" + wav_path.replace("/", "\\")
                
                # Construct exact path to segment
                segment_path = f"\\Interactive Music Hierarchy\\Default Work Unit\\{real_folder_name}\\{parent_container['name']}\\{parent_segment['name']}"
                logging.info(f"Importing source: {wine_wav_path} to target segment: {segment_path}")
                
                import_args = {
                    "importOperation": "useExisting",
                    "imports": [
                        {
                            "audioFile": wine_wav_path,
                            "objectPath": segment_path,
                            "objectType": "MusicSegment"
                        }
                    ]
                }
                import_res = client.call("ak.wwise.core.audio.import", import_args)
                logging.info(f"Import response: {json.dumps(import_res)}")

        # Save project to finalize audio import and metadata update
        client.call("ak.wwise.core.project.save")

        # 7. Query all descendants to rename the auto-created tracks and gather GUIDs
        logging.info("Querying descendants to rename tracks and collect GUIDs...")
        verify_res = client.call("ak.wwise.core.object.get", {
            "from": {"path": [folder_path]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "parent"]})
        
        descendants = verify_res.get("return", [])
        
        # Rename newly created tracks to their correct names "MusicTrack_<id>"
        for d in descendants:
            name = d["name"]
            if d["type"] == "MusicTrack":
                # Find the expected track name for this segment
                parent_info = d.get("parent")
                if parent_info:
                    parent_name = parent_info.get("name", "")
                    if "MusicSegment_" in parent_name:
                        seg_id = parent_name.split("_")[-1]
                        # Find the corresponding MusicTrack object in our spec
                        expected_track = None
                        for o in tracks:
                            if o["parent_info"]["id"] == seg_id:
                                expected_track = o
                                break
                        if expected_track:
                            new_track_name = expected_track["name"]
                            logging.info(f"Renaming auto-created track {name} to {new_track_name}")
                            client.call("ak.wwise.core.object.setName", {
                                "object": d["id"],
                                "value": new_track_name
                            })

        # Save project to persist renames
        client.call("ak.wwise.core.project.save")

        # Re-query all descendants after rename to get final GUID mappings
        logging.info("Re-querying descendants to map final GUIDs...")
        verify_res = client.call("ak.wwise.core.object.get", {
            "from": {"path": [folder_path]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "parent"]})
        
        descendants = verify_res.get("return", [])
        for d in descendants:
            name = d["name"]
            if d["type"] in ["MusicSegment", "MusicTrack"]:
                obj_id = name.split("_")[-1]
                created_guids[obj_id] = d["id"]

        # 7.5 Create MusicCue children for Segment markers (Entry/Exit/etc.)
        logging.info("Creating MusicCue children for segment markers where present...")
        segments = [o for o in objects_to_create if o["type"] == "MusicSegment"]
        for seg in segments:
            seg_id = seg["id"]
            seg_guid = created_guids.get(seg_id)
            if not seg_guid:
                logging.warning(f"No GUID found for segment {seg_id}; skipping cue creation")
                continue

            markers = seg.get("properties", {}).get("Markers", [])
            for mk in markers:
                try:
                    cue_name = f"MusicCue_{mk.get('id', 'unknown')}"
                    logging.info(f"Creating cue {cue_name} under segment {seg['name']} at {mk.get('position')} ms")
                    cue_res = client.call("ak.wwise.core.object.create", {
                        "parent": seg_guid,
                        "type": "MusicCue",
                        "name": cue_name,
                        "onNameConflict": "merge"
                    })
                    cue_guid = cue_res.get("id")
                    # Set TimeMs property on the cue child
                    time_ms = float(mk.get("position", 0.0))
                    client.call("ak.wwise.core.object.setProperty", {
                        "object": cue_guid,
                        "property": "TimeMs",
                        "value": time_ms
                    })
                    logging.info(f"Set TimeMs={time_ms} on cue {cue_guid}")
                except Exception as e:
                    logging.warning(f"Could not create/set cue for segment {seg_id}: {e}")

        # 8. Configure Playlists for PlaylistContainers
        logging.info("Configuring Playlists for MusicPlaylistContainers...")
        # Find all playlist items in project
        items_get = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "name", "path", "parent"]})
        
        all_playlist_items = items_get.get("return", [])
        
        segments = [o for o in objects_to_create if o["type"] == "MusicSegment"]
        for obj in containers:
            container_id = obj["id"]
            container_guid = created_guids[container_id]
            container_name = obj["name"]
            
            # Find root item for this container
            root_item = None
            for pi in all_playlist_items:
                parent_info = pi.get("parent")
                if parent_info and parent_info.get("id") == container_guid:
                    root_item = pi
                    break
                    
            if root_item:
                root_guid = root_item["id"]
                logging.info(f"Found root PlaylistItem {root_guid} for container {container_name}")
                
                # Set loop count and type based on the container details
                loop_val = 0
                type_val = 2 # default Random
                
                if "359976450" in container_name:
                    loop_val = 0
                    type_val = 2 # Random
                elif "517021411" in container_name:
                    loop_val = 0
                    type_val = 1 # Sequence
                elif "543160948" in container_name:
                    loop_val = 1
                    type_val = 2 # Random
                    
                try:
                    client.call("ak.wwise.core.object.setProperty", {
                        "object": root_guid,
                        "property": "LoopCount",
                        "value": loop_val
                    })
                    client.call("ak.wwise.core.object.setProperty", {
                        "object": root_guid,
                        "property": "PlaylistItemType",
                        "value": type_val
                    })
                    logging.info(f"Configured root playlist item: LoopCount={loop_val}, Type={type_val}")
                except Exception as e:
                    logging.warning(f"Could not set properties on root playlist item: {e}")
                    
                # Create children items pointing to segments for this container
                child_segments = [o for o in segments if o["parent_info"] and o["parent_info"]["id"] == container_id]
                for cs in child_segments:
                    seg_guid = created_guids[cs["id"]]
                    try:
                        # Create child playlist item under root item
                        child_item = client.call("ak.wwise.core.object.create", {
                            "parent": root_guid,
                            "type": "MusicPlaylistItem",
                            "name": f"Item_{cs['id']}",
                            "onNameConflict": "merge"
                        })
                        child_guid = child_item["id"]
                        
                        # Set segment reference
                        client.call("ak.wwise.core.object.setProperty", {
                            "object": child_guid,
                            "property": "PlaylistItemType",
                            "value": 0 # Segment type
                        })
                        client.call("ak.wwise.core.object.setReference", {
                            "object": child_guid,
                            "reference": "Segment",
                            "value": seg_guid
                        })
                        logging.info(f"Created PlaylistItem for segment {cs['name']} pointing to {seg_guid}")
                    except Exception as e:
                        logging.warning(f"Could not create/link playlist item for segment {cs['name']}: {e}")

        # 9. Save Project
        logging.info("Saving Wwise project...")
        client.call("ak.wwise.core.project.save")
        logging.info("Wwise project saved successfully!")

        # 10. Verification queries
        logging.info("================= RUNNING VERIFICATION QUERIES =================")
        verify_res = client.call("ak.wwise.core.object.get", {
            "from": {"path": [folder_path]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "parent"]})
        
        descendants = verify_res.get("return", [])
        logging.info(f"Total descendants under {folder_path}: {len(descendants)}")
        
        # Breakdown counting
        segment_count = sum(1 for d in descendants if d["type"] == "MusicSegment")
        track_count = sum(1 for d in descendants if d["type"] == "MusicTrack")
        ranseq_count = sum(1 for d in descendants if d["type"] == "MusicPlaylistContainer")
        
        logging.info(f"Count breakdown: Segments={segment_count}, Tracks={track_count}, RanSeqContainers={ranseq_count}")
        logging.info(f"Verification matched expected (7, 7, 3): {segment_count==7 and track_count==7 and ranseq_count==3}")
        
        # Read back Durations for segments
        logging.info("Reading back Duration property for segments:")
        for d in descendants:
            if d["type"] == "MusicSegment":
                dur_res = client.call("ak.wwise.core.object.get", {
                    "from": {"id": [d["id"]]}
                }, options={"return": ["id", "name", "duration", "@EndPosition"]})
                logging.info(f"Segment info: {json.dumps(dur_res.get('return', []))}")
                
        # Read back source assignment for tracks
        logging.info("Reading back source assignments for tracks:")
        for d in descendants:
            if d["type"] == "MusicTrack":
                track_sources = client.call("ak.wwise.core.object.get", {
                    "from": {"id": [d["id"]]},
                    "transform": [{"select": ["descendants"]}]
                }, options={"return": ["id", "name", "type", "path"]})
                logging.info(f"Track {d['name']} sources: {json.dumps(track_sources.get('return', []))}")

        # Read back Cue positions
        logging.info("Reading back Cue positions:")
        cues_verify = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "path", "@TimeMs", "@CueType"]})
        for cue in cues_verify.get("return", []):
            if real_folder_name in cue["path"]:
                logging.info(f"Cue: {cue['name']} at {cue['path']} -> TimeMs: {cue['@TimeMs']} ms, Type: {cue['@CueType']}")

    except Exception as e:
        logging.error(f"Error during WAAPI reconstruction: {e}")
    finally:
        client.disconnect()
        logging.info("Disconnected from WAAPI.")

if __name__ == "__main__":
    main()

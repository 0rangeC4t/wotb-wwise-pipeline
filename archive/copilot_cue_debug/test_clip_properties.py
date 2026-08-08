import os
import json
from waapi import WaapiClient

def main():
    try:
        client = WaapiClient()
        print("Connected to WAAPI")
        
        # 1. Create a test segment
        seg_res = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicSegment",
            "name": "TEST_CLIP_SEG",
            "onNameConflict": "replace"
        })
        seg_id = seg_res["id"]
        print("Created segment:", seg_id)
        
        # 2. Create track under segment
        track_res = client.call("ak.wwise.core.object.create", {
            "parent": seg_id,
            "type": "MusicTrack",
            "name": "TEST_CLIP_TRACK",
            "onNameConflict": "replace"
        })
        track_id = track_res["id"]
        print("Created track:", track_id)
        
        # 3. Import real audio file
        wav_file = os.path.abspath("out_wwise/wav_music/56953293.wav")
        wine_wav_path = "Z:" + wav_file.replace("/", "\\")
        print(f"Importing real audio: {wine_wav_path}")
        
        track_path = "\\Interactive Music Hierarchy\\Default Work Unit\\TEST_CLIP_SEG\\TEST_CLIP_TRACK"
        import_res = client.call("ak.wwise.core.audio.import", {
            "importOperation": "useExisting",
            "imports": [
                {
                    "audioFile": wine_wav_path,
                    "objectPath": track_path,
                    "objectType": "MusicTrack"
                }
            ]
        })
        print("Import response:", json.dumps(import_res, indent=2))
        
        client.call("ak.wwise.core.project.save")
        
        # 4. Get all descendants of the segment
        desc_res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_id]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "path", "@EndTrimOffset", "@TimeMs"]})
        print("Descendants of segment:", json.dumps(desc_res.get("return", []), indent=2))
        
        # Find clip and cues
        clip_id = None
        exit_cue_id = None
        for item in desc_res.get("return", []):
            if item["type"] == "MusicClip":
                clip_id = item["id"]
            elif item["type"] == "MusicCue" and item["name"] == "Exit Cue":
                exit_cue_id = item["id"]
                
        if clip_id:
            print(f"Trying to set EndTrimOffset on clip {clip_id} to 7680.0 ms...")
            client.call("ak.wwise.core.object.setProperty", {
                "object": clip_id,
                "property": "EndTrimOffset",
                "value": 7680.0
            })
            print("Successfully set EndTrimOffset!")
            
        if exit_cue_id:
            print(f"Trying to set TimeMs on Exit Cue {exit_cue_id} to 7680.0 ms...")
            client.call("ak.wwise.core.object.setProperty", {
                "object": exit_cue_id,
                "property": "TimeMs",
                "value": 7680.0
            })
            print("Successfully set Exit Cue TimeMs!")
            
        client.call("ak.wwise.core.project.save")
        
        # Read back descendants to verify
        read_back = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_id]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "@EndTrimOffset", "@TimeMs"]})
        print("After modification descendants:", json.dumps(read_back.get("return", []), indent=2))
        
        # Clean up
        client.call("ak.wwise.core.object.delete", {"object": seg_id})
        client.call("ak.wwise.core.project.save")
        print("Cleaned up.")
        
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == '__main__':
    main()

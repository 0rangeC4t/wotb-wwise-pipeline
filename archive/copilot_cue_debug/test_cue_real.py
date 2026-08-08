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
            "name": "TEST_REAL_SEG",
            "onNameConflict": "replace"
        })
        seg_id = seg_res["id"]
        print("Created segment:", seg_id)
        
        # 2. Create track under segment
        track_res = client.call("ak.wwise.core.object.create", {
            "parent": seg_id,
            "type": "MusicTrack",
            "name": "TEST_REAL_TRACK",
            "onNameConflict": "replace"
        })
        track_id = track_res["id"]
        print("Created track:", track_id)
        
        # 3. Import real audio file
        wav_file = os.path.abspath("out_wwise/wav_music/56953293.wav")
        wine_wav_path = "Z:" + wav_file.replace("/", "\\")
        print(f"Importing real audio: {wine_wav_path}")
        
        track_path = "\\Interactive Music Hierarchy\\Default Work Unit\\TEST_REAL_SEG\\TEST_REAL_TRACK"
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
        
        # 4. Find the Exit Cue
        cues_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "path", "@TimeMs"]})
        
        exit_cue_id = None
        for cue in cues_res.get("return", []):
            if "TEST_REAL_SEG" in cue["path"] and cue["name"] == "Exit Cue":
                exit_cue_id = cue["id"]
                print("Found Exit Cue:", cue)
                
        if exit_cue_id:
            # Let's try setting TimeMs to 7680.0
            print("Trying to set Exit Cue TimeMs to 7680.0 ms...")
            client.call("ak.wwise.core.object.setProperty", {
                "object": exit_cue_id,
                "property": "TimeMs",
                "value": 7680.0
            })
            print("Successfully set TimeMs!")
            
            client.call("ak.wwise.core.project.save")
            
            # Read back
            read_back = client.call("ak.wwise.core.object.get", {
                "from": {"id": [exit_cue_id]}
            }, options={"return": ["id", "name", "path", "@TimeMs"]})
            print("After set:", read_back.get("return", []))
            
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

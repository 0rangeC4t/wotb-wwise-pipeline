import os
import json
from waapi import WaapiClient

def main():
    try:
        client = WaapiClient()
        print("Connected to WAAPI")
        
        # 1. Clean up any existing TEST_IMPORT_SEG
        try:
            client.call("ak.wwise.core.object.delete", {"object": "\\Interactive Music Hierarchy\\Default Work Unit\\TEST_IMPORT_SEG"})
        except Exception:
            pass
            
        # 2. Import a real audio file as a MusicSegment!
        wav_file = os.path.abspath("out_wwise/wav_music/56953293.wav")
        wine_wav_path = "Z:" + wav_file.replace("/", "\\")
        segment_path = "\\Interactive Music Hierarchy\\Default Work Unit\\TEST_IMPORT_SEG"
        
        import_res = client.call("ak.wwise.core.audio.import", {
            "importOperation": "useExisting",
            "imports": [
                {
                    "audioFile": wine_wav_path,
                    "objectPath": segment_path,
                    "objectType": "MusicSegment"
                }
            ]
        })
        print("Import response:", json.dumps(import_res, indent=2))
        client.call("ak.wwise.core.project.save")
        
        # 3. Find the created track under the segment
        desc_res = client.call("ak.wwise.core.object.get", {
            "from": {"path": [segment_path]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type"]})
        
        track_id = None
        for item in desc_res.get("return", []):
            if item["type"] == "MusicTrack":
                track_id = item["id"]
                print("Found Track:", item)
                
        # 4. Rename the track
        if track_id:
            print("Renaming track to MusicTrack_558864082...")
            client.call("ak.wwise.core.object.setName", {
                "object": track_id,
                "value": "MusicTrack_558864082"
            })
            print("Rename successful!")
            
        client.call("ak.wwise.core.project.save")
        
        # 5. Read back cues and descendants
        res_after = client.call("ak.wwise.core.object.get", {
            "from": {"path": [segment_path]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type"]})
        print("Descendants after rename:", res_after.get("return", []))
        
        cues_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "type", "path", "@TimeMs"]})
        for cue in cues_res.get("return", []):
            if "TEST_IMPORT_SEG" in cue["path"]:
                print("Cue after rename:", cue)
                
        # Clean up
        client.call("ak.wwise.core.object.delete", {"object": segment_path})
        client.call("ak.wwise.core.project.save")
        print("Cleaned up.")
        
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == '__main__':
    main()

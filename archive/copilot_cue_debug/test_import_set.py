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
            
        # 2. Import a real audio file
        wav_file = os.path.abspath("out_wwise/wav_music/56953293.wav")
        wine_wav_path = "Z:" + wav_file.replace("/", "\\")
        track_path = "\\Interactive Music Hierarchy\\Default Work Unit\\TEST_IMPORT_SEG\\TEST_IMPORT_TRACK"
        
        client.call("ak.wwise.core.audio.import", {
            "importOperation": "useExisting",
            "imports": [
                {
                    "audioFile": wine_wav_path,
                    "objectPath": track_path,
                    "objectType": "MusicTrack"
                }
            ]
        })
        client.call("ak.wwise.core.project.save")
        
        # 3. Find Exit Cue
        cues_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "type", "path", "@TimeMs"]})
        
        exit_cue_id = None
        for cue in cues_res.get("return", []):
            if "TEST_IMPORT_SEG" in cue["path"] and cue["name"] == "Exit Cue":
                exit_cue_id = cue["id"]
                print("Exit cue before:", cue)
                
        # 4. Try to set Exit Cue position to 7680.0 ms
        if exit_cue_id:
            print("Trying to set Exit Cue TimeMs to 7680.0 ms...")
            client.call("ak.wwise.core.object.setProperty", {
                "object": exit_cue_id,
                "property": "TimeMs",
                "value": 7680.0
            })
            print("Successfully set Exit Cue TimeMs!")
            client.call("ak.wwise.core.project.save")
            
            # Read back
            cue_after = client.call("ak.wwise.core.object.get", {
                "from": {"id": [exit_cue_id]}
            }, options={"return": ["id", "name", "@TimeMs"]})
            print("Exit Cue after:", cue_after.get("return", []))
            
        # Clean up
        client.call("ak.wwise.core.object.delete", {"object": "\\Interactive Music Hierarchy\\Default Work Unit\\TEST_IMPORT_SEG"})
        client.call("ak.wwise.core.project.save")
        print("Cleaned up.")
        
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == '__main__':
    main()

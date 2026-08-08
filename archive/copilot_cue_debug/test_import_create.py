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
            
        # 2. Import a real audio file (this should create the parent MusicSegment and MusicTrack)
        wav_file = os.path.abspath("out_wwise/wav_music/56953293.wav")
        wine_wav_path = "Z:" + wav_file.replace("/", "\\")
        print(f"Importing and creating hierarchy for: {wine_wav_path}")
        
        track_path = "\\Interactive Music Hierarchy\\Default Work Unit\\TEST_IMPORT_SEG\\TEST_IMPORT_TRACK"
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
        
        # 3. Read back properties of the created segment and its Exit Cue
        seg_res = client.call("ak.wwise.core.object.get", {
            "from": {"path": ["\\Interactive Music Hierarchy\\Default Work Unit\\TEST_IMPORT_SEG"]}
        }, options={"return": ["id", "name", "@EndPosition"]})
        print("Created Segment:", seg_res.get("return", []))
        
        cues_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "type", "path", "@TimeMs"]})
        
        for cue in cues_res.get("return", []):
            if "TEST_IMPORT_SEG" in cue["path"]:
                print("Found cue for TEST_IMPORT_SEG:", cue)
                
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

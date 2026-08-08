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
            "name": "TEST_CLIP_SET",
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
        
        track_path = "\\Interactive Music Hierarchy\\Default Work Unit\\TEST_CLIP_SET\\TEST_CLIP_TRACK"
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
        
        # 4. Get all clips
        clips_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicClip"]}
        }, options={"return": ["id", "name", "type", "path", "@EndTrimOffset"]})
        
        clip_id = None
        for clip in clips_res.get("return", []):
            if "TEST_CLIP_SET" in clip["path"]:
                clip_id = clip["id"]
                print("Found Clip before:", clip)
                
        # 5. Get Exit Cue
        cues_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "type", "path", "@TimeMs"]})
        
        exit_cue_id = None
        for cue in cues_res.get("return", []):
            if "TEST_CLIP_SET" in cue["path"] and cue["name"] == "Exit Cue":
                exit_cue_id = cue["id"]
                print("Found Exit Cue before:", cue)
                
        # 6. Try to set EndTrimOffset first
        if clip_id:
            print("Setting EndTrimOffset to 7680.0 ms...")
            client.call("ak.wwise.core.object.setProperty", {
                "object": clip_id,
                "property": "EndTrimOffset",
                "value": 7680.0
            })
            print("Successfully set EndTrimOffset!")
            
        # 7. Try to set Exit Cue position
        if exit_cue_id:
            print("Setting Exit Cue TimeMs to 7680.0 ms...")
            client.call("ak.wwise.core.object.setProperty", {
                "object": exit_cue_id,
                "property": "TimeMs",
                "value": 7680.0
            })
            print("Successfully set Exit Cue TimeMs!")
            
        client.call("ak.wwise.core.project.save")
        
        # 8. Read back
        if clip_id:
            clip_after = client.call("ak.wwise.core.object.get", {
                "from": {"id": [clip_id]}
            }, options={"return": ["id", "name", "@EndTrimOffset"]})
            print("Clip after:", clip_after.get("return", []))
            
        if exit_cue_id:
            cue_after = client.call("ak.wwise.core.object.get", {
                "from": {"id": [exit_cue_id]}
            }, options={"return": ["id", "name", "@TimeMs"]})
            print("Cue after:", cue_after.get("return", []))
            
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

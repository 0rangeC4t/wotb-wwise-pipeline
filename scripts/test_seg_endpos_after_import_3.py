import os
from waapi import WaapiClient
import pprint

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        # Create container
        container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "Test_Cntr_EndPos_ClipOrder3",
            "onNameConflict": "replace"
        })
        container_guid = container["id"]
        
        # Import a wav file
        wav_path = os.path.abspath("out_wwise/wav_music/175220409.wav")
        wine_wav_path = "Z:" + wav_path.replace("/", "\\")
        segment_path = "\\Interactive Music Hierarchy\\Default Work Unit\\Test_Cntr_EndPos_ClipOrder3\\Test_Seg_ClipOrder3"
        
        print(f"Importing {wine_wav_path} to {segment_path}...")
        client.call("ak.wwise.core.audio.import", {
            "importOperation": "useExisting",
            "imports": [
                {
                    "audioFile": wine_wav_path,
                    "objectPath": segment_path,
                    "objectType": "MusicSegment"
                }
            ]
        })
        
        client.call("ak.wwise.core.project.save")
        
        # Find GUIDs
        seg_res = client.call("ak.wwise.core.object.get", {
            "from": {"path": [segment_path]}
        }, options={"return": ["id"]})
        seg_guid = seg_res["return"][0]["id"]
        
        # Find MusicClip globally
        all_clips = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicClip"]}
        }, options={"return": ["id", "name", "path"]})
        
        clip_guid = None
        for clip in all_clips.get("return", []):
            if "Test_Seg_ClipOrder3" in clip["path"]:
                clip_guid = clip["id"]
                break
                
        # Find Exit Cue globally
        all_cues = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "@CueType", "path"]})
        
        exit_cue_guid = None
        for cue in all_cues.get("return", []):
            if "Test_Seg_ClipOrder3" in cue["path"] and cue["@CueType"] == 1:
                exit_cue_guid = cue["id"]
                break
                
        print(f"Segment GUID: {seg_guid}")
        print(f"Exit Cue GUID: {exit_cue_guid}")
        print(f"MusicClip GUID: {clip_guid}")
        
        target_val = 31035.290348023253
        
        # Set Clip EndTrimOffset
        if clip_guid:
            print(f"\n1. Setting EndTrimOffset on MusicClip...")
            try:
                client.call("ak.wwise.core.object.setProperty", {
                    "object": clip_guid,
                    "property": "EndTrimOffset",
                    "value": target_val
                })
                print("SUCCESS setting clip EndTrimOffset!")
            except Exception as e:
                print("FAILED setting clip EndTrimOffset:", e)
                
        # Set Exit Cue TimeMs
        if exit_cue_guid:
            print(f"\n2. Setting TimeMs on Exit Cue...")
            try:
                client.call("ak.wwise.core.object.setProperty", {
                    "object": exit_cue_guid,
                    "property": "TimeMs",
                    "value": target_val
                })
                print("SUCCESS setting Exit Cue TimeMs!")
            except Exception as e:
                print("FAILED setting Exit Cue TimeMs:", e)
                
        # Set Segment EndPosition
        print(f"\n3. Setting EndPosition on MusicSegment...")
        try:
            client.call("ak.wwise.core.object.setProperty", {
                "object": seg_guid,
                "property": "EndPosition",
                "value": target_val
            })
            print("SUCCESS setting segment EndPosition!")
        except Exception as e:
            print("FAILED setting segment EndPosition:", e)
            
        client.call("ak.wwise.core.project.save")
        
        # Read back
        print("\n=== READBACK ===")
        seg_rb = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["@EndPosition"]})
        print("Segment EndPosition:", seg_rb["return"][0]["@EndPosition"])
        
        if exit_cue_guid:
            cue_rb = client.call("ak.wwise.core.object.get", {
                "from": {"id": [exit_cue_guid]}
            }, options={"return": ["@TimeMs"]})
            print("Exit Cue TimeMs:", cue_rb["return"][0]["@TimeMs"])
            
        if clip_guid:
            clip_rb = client.call("ak.wwise.core.object.get", {
                "from": {"id": [clip_guid]}
            }, options={"return": ["@EndTrimOffset"]})
            print("Clip EndTrimOffset:", clip_rb["return"][0]["@EndTrimOffset"])
            
    finally:
        client.call("ak.wwise.core.object.delete", {"object": container_guid})
        client.call("ak.wwise.core.project.save")
        
    client.disconnect()

if __name__ == "__main__":
    main()

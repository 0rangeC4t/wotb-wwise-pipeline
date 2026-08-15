from waapi import WaapiClient
import time

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    seg_guid = "{5D36B392-C77A-48FB-AE96-775B42CED15B}" # MusicSegment_860825692
    duration = 31035.290348023253
    
    try:
        # Step 1: Set Clip EndTrimOffset
        res_clips = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicClip"]}
        }, options={"return": ["id", "name", "path"]})
        
        segment_name = "MusicSegment_860825692"
        clips = [c for c in res_clips.get("return", []) if segment_name in c["path"]]
        
        print(f"Setting {len(clips)} clips' EndTrimOffset...")
        for clip in clips:
            client.call("ak.wwise.core.object.setProperty", {
                "object": clip["id"],
                "property": "EndTrimOffset",
                "value": duration
            })
            
        # Save project first!
        print("Saving project after setting Clip EndTrimOffsets...")
        client.call("ak.wwise.core.project.save")
        
        # Step 2: Set Exit Cue TimeMs
        all_cues = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "@CueType", "path"]})
        
        exit_cue_guid = None
        for cue in all_cues.get("return", []):
            if segment_name in cue["path"] and cue["@CueType"] == 1:
                exit_cue_guid = cue["id"]
                break
                
        if exit_cue_guid:
            print(f"Setting Exit Cue TimeMs to {duration}...")
            client.call("ak.wwise.core.object.setProperty", {
                "object": exit_cue_guid,
                "property": "TimeMs",
                "value": duration
            })
            
        # Step 3: Set Segment EndPosition
        print(f"Setting Segment EndPosition to {duration}...")
        client.call("ak.wwise.core.object.setProperty", {
            "object": seg_guid,
            "property": "EndPosition",
            "value": duration
        })
        
        # Save project again!
        print("Saving project after setting Cue and Segment...")
        client.call("ak.wwise.core.project.save")
        
        # Read back read-backs
        res_seg = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["id", "name", "@EndPosition"]})
        print("Read-back Segment EndPosition:", res_seg["return"][0]["@EndPosition"])
        
        if exit_cue_guid:
            res_cue = client.call("ak.wwise.core.object.get", {
                "from": {"id": [exit_cue_guid]}
            }, options={"return": ["id", "name", "@TimeMs"]})
            print("Read-back Exit Cue TimeMs:", res_cue["return"][0]["@TimeMs"])
            
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

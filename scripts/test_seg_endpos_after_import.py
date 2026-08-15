import os
from waapi import WaapiClient

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        # Create container
        container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "Test_Cntr_EndPos_AfterImport",
            "onNameConflict": "replace"
        })
        container_guid = container["id"]
        
        # Import a wav file (creates the segment Test_Seg_EndPos_AfterImport)
        wav_path = os.path.abspath("out_wwise/wav_music/175220409.wav")
        wine_wav_path = "Z:" + wav_path.replace("/", "\\")
        segment_path = "\\Interactive Music Hierarchy\\Default Work Unit\\Test_Cntr_EndPos_AfterImport\\Test_Seg_EndPos_AfterImport"
        
        print(f"Importing {wine_wav_path} to {segment_path}...")
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
        client.call("ak.wwise.core.audio.import", import_args)
        
        # Save project
        client.call("ak.wwise.core.project.save")
        
        # Query segment GUID
        seg_res = client.call("ak.wwise.core.object.get", {
            "from": {"path": [segment_path]}
        }, options={"return": ["id"]})
        seg_guid = seg_res["return"][0]["id"]
        
        # Read EndPosition and Exit Cue TimeMs before
        res_before = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["@EndPosition"]})
        print("Segment EndPosition before setting:", res_before["return"][0]["@EndPosition"])
        
        # Find Exit Cue
        all_cues = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "@CueType", "path"]})
        
        exit_cue_guid = None
        for cue in all_cues.get("return", []):
            if "Test_Seg_EndPos_AfterImport" in cue["path"] and cue["@CueType"] == 1:
                exit_cue_guid = cue["id"]
                break
                
        if exit_cue_guid:
            # Set Exit Cue TimeMs
            print(f"Setting Exit Cue TimeMs to 31035.29...")
            try:
                client.call("ak.wwise.core.object.setProperty", {
                    "object": exit_cue_guid,
                    "property": "TimeMs",
                    "value": 31035.29
                })
                print("Exit Cue TimeMs set call executed.")
            except Exception as e:
                print("Exit Cue TimeMs set failed:", e)
                
        # Set Segment EndPosition
        print("Setting segment EndPosition to 31035.29...")
        try:
            client.call("ak.wwise.core.object.setProperty", {
                "object": seg_guid,
                "property": "EndPosition",
                "value": 31035.29
            })
            print("Segment EndPosition set call executed.")
        except Exception as e:
            print("Segment EndPosition set failed:", e)
            
        # Save project
        client.call("ak.wwise.core.project.save")
        
        # Read after
        res_after = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["@EndPosition"]})
        print("Segment EndPosition after:", res_after["return"][0]["@EndPosition"])
        
        if exit_cue_guid:
            cue_after = client.call("ak.wwise.core.object.get", {
                "from": {"id": [exit_cue_guid]}
            }, options={"return": ["@TimeMs"]})
            print("Exit Cue TimeMs after:", cue_after["return"][0]["@TimeMs"])
            
    finally:
        client.call("ak.wwise.core.object.delete", {"object": container_guid})
        client.call("ak.wwise.core.project.save")
        
    client.disconnect()

if __name__ == "__main__":
    main()

from waapi import WaapiClient

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "Test_Cntr_Cue_Duration",
            "onNameConflict": "replace"
        })
        container_guid = container["id"]
        
        seg = client.call("ak.wwise.core.object.create", {
            "parent": container_guid,
            "type": "MusicSegment",
            "name": "Test_Seg_Cue_Duration",
            "onNameConflict": "replace"
        })
        seg_guid = seg["id"]
        
        # Query children of segment to find the Exit Cue
        cues_res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]},
            "transform": [{"select": ["children"]}]
        }, options={"return": ["id", "name", "type", "@CueType", "@TimeMs"]})
        
        cues = cues_res.get("return", [])
        exit_cue_guid = None
        for cue in cues:
            if cue["type"] == "MusicCue" and cue["@CueType"] == 1: # Exit Cue
                exit_cue_guid = cue["id"]
                break
                
        if not exit_cue_guid:
            print("ERROR: Exit Cue not found.")
            return
            
        print(f"Found Exit Cue: {exit_cue_guid}")
        
        # Read before
        res_before = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["@EndPosition"]})
        print("EndPosition before setting Exit Cue:", res_before["return"][0]["@EndPosition"])
        
        # Set Exit Cue TimeMs
        print("Setting Exit Cue TimeMs to 31035.29...")
        client.call("ak.wwise.core.object.setProperty", {
            "object": exit_cue_guid,
            "property": "TimeMs",
            "value": 31035.29
        })
        print("Successfully set Exit Cue TimeMs.")
        
        # Read after
        res_after = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["@EndPosition"]})
        print("EndPosition after setting Exit Cue:", res_after["return"][0]["@EndPosition"])
        
        # Also read Exit Cue TimeMs after
        cue_after = client.call("ak.wwise.core.object.get", {
            "from": {"id": [exit_cue_guid]}
        }, options={"return": ["@TimeMs"]})
        print("Exit Cue TimeMs readback:", cue_after["return"][0]["@TimeMs"])
        
    finally:
        client.call("ak.wwise.core.object.delete", {"object": container_guid})
        client.call("ak.wwise.core.project.save")
        
    client.disconnect()

if __name__ == "__main__":
    main()

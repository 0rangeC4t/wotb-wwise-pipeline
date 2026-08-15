from waapi import WaapiClient

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "Test_Cntr_Cue_By_Path",
            "onNameConflict": "replace"
        })
        container_guid = container["id"]
        
        seg = client.call("ak.wwise.core.object.create", {
            "parent": container_guid,
            "type": "MusicSegment",
            "name": "Test_Seg_Cue_By_Path",
            "onNameConflict": "replace"
        })
        seg_guid = seg["id"]
        
        # Save project
        client.call("ak.wwise.core.project.save")
        
        # Query all cues
        all_cues = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "@CueType", "path"]})
        
        exit_cue_guid = None
        for cue in all_cues.get("return", []):
            if "Test_Seg_Cue_By_Path" in cue["path"] and cue["@CueType"] == 1:
                exit_cue_guid = cue["id"]
                break
                
        if not exit_cue_guid:
            print("ERROR: Exit Cue not found.")
            return
            
        print(f"Found Exit Cue GUID: {exit_cue_guid}")
        
        # Read segment EndPosition before
        res_before = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["@EndPosition"]})
        print("Segment EndPosition before:", res_before["return"][0]["@EndPosition"])
        
        # Set Exit Cue TimeMs
        print("Setting Exit Cue TimeMs to 31035.29...")
        client.call("ak.wwise.core.object.setProperty", {
            "object": exit_cue_guid,
            "property": "TimeMs",
            "value": 31035.29
        })
        print("Set Exit Cue TimeMs successfully!")
        
        # Read segment EndPosition after
        res_after = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["@EndPosition"]})
        print("Segment EndPosition after:", res_after["return"][0]["@EndPosition"])
        
    finally:
        client.call("ak.wwise.core.object.delete", {"object": container_guid})
        client.call("ak.wwise.core.project.save")
        
    client.disconnect()

if __name__ == "__main__":
    main()

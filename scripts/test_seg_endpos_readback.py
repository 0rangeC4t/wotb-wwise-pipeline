from waapi import WaapiClient

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "Test_Cntr_EndPos_Readback",
            "onNameConflict": "replace"
        })
        container_guid = container["id"]
        
        seg = client.call("ak.wwise.core.object.create", {
            "parent": container_guid,
            "type": "MusicSegment",
            "name": "Test_Seg_EndPos_Readback",
            "onNameConflict": "replace"
        })
        seg_guid = seg["id"]
        
        # Read before
        res_before = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["@EndPosition"]})
        print("EndPosition before:", res_before["return"][0]["@EndPosition"])
        
        # Set EndPosition
        print("Setting EndPosition...")
        try:
            res_set = client.call("ak.wwise.core.object.setProperty", {
                "object": seg_guid,
                "property": "EndPosition",
                "value": 31035.29
            })
            print("Set result:", res_set)
        except Exception as e:
            print("Set failed with exception:", e)
            
        # Read after
        res_after = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["@EndPosition"]})
        print("EndPosition after:", res_after["return"][0]["@EndPosition"])
        
    finally:
        client.call("ak.wwise.core.object.delete", {"object": container_guid})
        client.call("ak.wwise.core.project.save")
        
    client.disconnect()

if __name__ == "__main__":
    main()

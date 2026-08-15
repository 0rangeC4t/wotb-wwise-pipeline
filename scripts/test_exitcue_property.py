from waapi import WaapiClient
import pprint

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "Test_Cntr_ExitCueProp",
            "onNameConflict": "replace"
        })
        container_guid = container["id"]
        
        seg = client.call("ak.wwise.core.object.create", {
            "parent": container_guid,
            "type": "MusicSegment",
            "name": "Test_Seg_ExitCueProp",
            "onNameConflict": "replace"
        })
        seg_guid = seg["id"]
        
        # Get all properties/references of MusicSegment
        props = client.call("ak.wwise.core.object.getPropertyAndReferenceNames", {
            "object": seg_guid
        })
        print("Segment Properties & References:")
        pprint.pprint(props.get("return", []))
        
        # Try setting ExitCue property directly on segment
        print("\nSetting ExitCue to 31035.29 on segment...")
        try:
            client.call("ak.wwise.core.object.setProperty", {
                "object": seg_guid,
                "property": "ExitCue",
                "value": 31035.29
            })
            print("Successfully set ExitCue property!")
        except Exception as e:
            print("Failed to set ExitCue property:", e)
            
        # Read back properties
        readback = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]}
        }, options={"return": ["@ExitCue", "@EndPosition"]})
        print("\nReadback:")
        pprint.pprint(readback.get("return", []))
        
    finally:
        client.call("ak.wwise.core.object.delete", {"object": container_guid})
        client.call("ak.wwise.core.project.save")
        
    client.disconnect()

if __name__ == "__main__":
    main()

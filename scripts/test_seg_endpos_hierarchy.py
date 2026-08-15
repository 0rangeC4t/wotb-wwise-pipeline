import json
from waapi import WaapiClient

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "Test_Cntr_EndPos",
            "onNameConflict": "replace"
        })
        container_guid = container["id"]
        
        seg = client.call("ak.wwise.core.object.create", {
            "parent": container_guid,
            "type": "MusicSegment",
            "name": "Test_Seg_EndPos",
            "onNameConflict": "replace"
        })
        seg_guid = seg["id"]
        
        # Try setting EndPosition
        print("Setting EndPosition...")
        client.call("ak.wwise.core.object.setProperty", {
            "object": seg_guid,
            "property": "EndPosition",
            "value": 31035.290348023253
        })
        print("Success setting EndPosition!")
        
    except Exception as e:
        print("Failed:", e)
    finally:
        client.call("ak.wwise.core.object.delete", {"object": container_guid})
        client.call("ak.wwise.core.project.save")
        
    client.disconnect()

if __name__ == "__main__":
    main()

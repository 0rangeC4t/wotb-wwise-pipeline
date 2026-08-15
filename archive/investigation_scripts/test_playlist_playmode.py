import json
import pprint
from waapi import WaapiClient

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        # Create container
        container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "Test_Cntr_PlayMode_Investigation",
            "onNameConflict": "replace"
        })
        container_guid = container["id"]
        
        # Save project to ensure playlist root is generated
        client.call("ak.wwise.core.project.save")
        
        # Find root item
        items_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "owner"]})
        
        root_guid = None
        for item in items_res.get("return", []):
            owner = item.get("owner")
            if owner and owner.get("id") == container_guid:
                root_guid = item["id"]
                break
                
        if not root_guid:
            print("ERROR: Root PlaylistItem not found!")
            return
            
        # Create a group under root
        group = client.call("ak.wwise.core.object.create", {
            "parent": root_guid,
            "type": "MusicPlaylistItem",
            "name": "TestGroup",
            "onNameConflict": "replace"
        })
        g_guid = group["id"]
        
        # Set PlaylistItemType to 1 (Group)
        client.call("ak.wwise.core.object.setProperty", {
            "object": g_guid,
            "property": "PlaylistItemType",
            "value": 1
        })
        
        # Try setting PlayMode to different values (0, 1, 2, 3, 4, 5, etc.)
        print("\nTesting PlayMode values on Group (PlaylistItemType = 1):")
        for pm_val in range(10):
            try:
                client.call("ak.wwise.core.object.setProperty", {
                    "object": g_guid,
                    "property": "PlayMode",
                    "value": pm_val
                })
                # Read back path to see if Wwise changes the path name based on PlayMode!
                # For example, path contains "[1. Sequence Continuous Group]" or similar
                verify = client.call("ak.wwise.core.object.get", {
                    "from": {"id": [g_guid]}
                }, options={"return": ["@PlayMode", "path"]})
                print(f"Set PlayMode to {pm_val} -> Readback: {verify['return'][0]['@PlayMode']}, Path: {verify['return'][0]['path']}")
            except Exception as e:
                print(f"Failed to set PlayMode to {pm_val}: {e}")
                
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        try:
            client.call("ak.wwise.core.object.delete", {"object": container_guid})
            print("Deleted container.")
            client.call("ak.wwise.core.project.save")
        except Exception as e:
            print(f"Cleanup error: {e}")
            
    client.disconnect()

if __name__ == "__main__":
    main()

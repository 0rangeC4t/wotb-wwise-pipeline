import json
import pprint
from waapi import WaapiClient

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected to WAAPI.")
    
    try:
        # Create a container
        container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "Test_Cntr_Playlist_Investigation",
            "onNameConflict": "replace"
        })
        container_guid = container["id"]
        print(f"Created container: {container_guid}")
        
        # Save project to ensure the playlist structure is generated
        client.call("ak.wwise.core.project.save")
        
        # Get all playlist items in project
        items_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "name", "owner", "path"]})
        
        # Find root item
        root_guid = None
        for item in items_res.get("return", []):
            owner = item.get("owner")
            if owner and owner.get("id") == container_guid:
                root_guid = item["id"]
                break
                
        if not root_guid:
            print("ERROR: Root PlaylistItem not found!")
            return
            
        print(f"Found Root PlaylistItem: {root_guid}")
        
        # Let's inspect root properties
        root_props_before = client.call("ak.wwise.core.object.get", {
            "from": {"id": [root_guid]}
        }, options={"return": [
            "id", "name", "path",
            "@PlaylistItemType", "@PlayMode", "@LoopCount", "@NormalOrShuffle", "@Weight"
        ]})
        print("\nRoot item properties before setting:")
        pprint.pprint(root_props_before.get("return", []))
        
        # Try creating nested items under root
        print("\nCreating child items under root...")
        
        # 1. Group A (MusicPlaylistItem)
        group_a = client.call("ak.wwise.core.object.create", {
            "parent": root_guid,
            "type": "MusicPlaylistItem",
            "name": "Group_A",
            "onNameConflict": "replace"
        })
        ga_guid = group_a["id"]
        print(f"Created Group A: {ga_guid}")
        
        # 2. Segment Item under Group A
        seg_item = client.call("ak.wwise.core.object.create", {
            "parent": ga_guid,
            "type": "MusicPlaylistItem",
            "name": "Item_Seg_1",
            "onNameConflict": "replace"
        })
        seg_guid = seg_item["id"]
        print(f"Created Segment Item under Group A: {seg_guid}")
        
        # Now let's try setting properties on Group A
        # Properties to test: PlaylistItemType, LoopCount, Weight, NormalOrShuffle, PlayMode
        # Let's set LoopCount = 5, PlaylistItemType = 2 (Random Continuous), Weight = 75.5
        print("\nSetting properties on Group A...")
        
        client.call("ak.wwise.core.object.setProperty", {
            "object": ga_guid,
            "property": "PlaylistItemType",
            "value": 2
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": ga_guid,
            "property": "LoopCount",
            "value": 5
        })
        client.call("ak.wwise.core.object.setProperty", {
            "object": ga_guid,
            "property": "Weight",
            "value": 75.5
        })
        
        # Let's read back Group A properties
        ga_props_after = client.call("ak.wwise.core.object.get", {
            "from": {"id": [ga_guid]}
        }, options={"return": [
            "id", "name", "path",
            "@PlaylistItemType", "@PlayMode", "@LoopCount", "@NormalOrShuffle", "@Weight"
        ]})
        print("\nGroup A properties after setting:")
        pprint.pprint(ga_props_after.get("return", []))
        
        # Let's verify what values PlaylistItemType can take:
        # Segment: 0? Sequence Continuous: 1? Random Continuous: 2? Sequence Step: 3? Random Step: 4?
        for t_val in [0, 1, 2, 3, 4]:
            try:
                client.call("ak.wwise.core.object.setProperty", {
                    "object": ga_guid,
                    "property": "PlaylistItemType",
                    "value": t_val
                })
                verify = client.call("ak.wwise.core.object.get", {
                    "from": {"id": [ga_guid]}
                }, options={"return": ["@PlaylistItemType"]})
                print(f"Set PlaylistItemType to {t_val} -> Readback: {verify['return'][0]['@PlaylistItemType']}")
            except Exception as e:
                print(f"Failed to set PlaylistItemType to {t_val}: {e}")
                
        # Let's test setting NormalOrShuffle
        # 0 = Shuffle? 1 = Normal?
        for ns_val in [0, 1]:
            try:
                client.call("ak.wwise.core.object.setProperty", {
                    "object": ga_guid,
                    "property": "NormalOrShuffle",
                    "value": ns_val
                })
                verify = client.call("ak.wwise.core.object.get", {
                    "from": {"id": [ga_guid]}
                }, options={"return": ["@NormalOrShuffle"]})
                print(f"Set NormalOrShuffle to {ns_val} -> Readback: {verify['return'][0]['@NormalOrShuffle']}")
            except Exception as e:
                print(f"Failed to set NormalOrShuffle to {ns_val}: {e}")
                
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

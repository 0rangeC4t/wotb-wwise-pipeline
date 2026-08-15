import json
import pprint
from waapi import WaapiClient

def investigate():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected to WAAPI.")
    
    try:
        # Create a throwaway MusicPlaylistContainer
        temp_container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "ThrowawayPlaylistContainer_Investigate",
            "onNameConflict": "replace"
        })
        container_guid = temp_container["id"]
        print(f"Created container: {container_guid}")
        
        # Get the auto-created root playlist item
        playlist_items_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "name", "type", "parent"]})
        
        root_items = [pi for pi in playlist_items_res.get("return", []) if pi.get("parent", {}).get("id") == container_guid]
        if not root_items:
            print("ERROR: Root PlaylistItem not found.")
            return
            
        root_guid = root_items[0]["id"]
        print(f"Found root PlaylistItem: {root_guid}")
        
        # Introspect property and reference names for MusicPlaylistItem
        props_res = client.call("ak.wwise.core.object.getPropertyAndReferenceNames", {
            "object": root_guid
        })
        print("\nAvailable Properties and References:")
        pprint.pprint(props_res)
        
        # Now let's try creating a nested group and a nested segment item
        # Create Group A under root
        group_a = client.call("ak.wwise.core.object.create", {
            "parent": root_guid,
            "type": "MusicPlaylistItem",
            "name": "TestGroup_A",
            "onNameConflict": "replace"
        })
        ga_guid = group_a["id"]
        print(f"\nCreated group item under root: {ga_guid}")
        
        # Query properties of a newly created item to see their default values and types
        query_res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [ga_guid]}
        }, options={"return": [
            "id", "name",
            "@PlaylistItemType",
            "@PlayMode",
            "@LoopCount",
            "@NormalOrShuffle",
            "@Weight",
            "@RandomAvoidRepeatingCount"
        ]})
        print("\nDefault property values:")
        pprint.pprint(query_res.get("return", []))
        
        # Let's test setting property names:
        # LoopCount (int32/int16/double? let's check)
        # PlaylistItemType (0=Segment, 1=Sequence Continuous, 2=Random Continuous, 3=Sequence Step, 4=Random Step?)
        # Let's try to set these properties and see what works
        test_properties = [
            ("PlaylistItemType", 2),
            ("LoopCount", 0),
            ("Weight", 45.5),
            ("NormalOrShuffle", 0), # Shuffle? Let's check values
            ("NormalOrShuffle", 1), # Normal?
            ("PlayMode", 1),
        ]
        
        print("\nTesting setting properties:")
        for prop, val in test_properties:
            try:
                client.call("ak.wwise.core.object.setProperty", {
                    "object": ga_guid,
                    "property": prop,
                    "value": val
                })
                print(f"SUCCESS: Set {prop} to {val}")
            except Exception as e:
                print(f"FAILED: Set {prop} to {val}: {e}")
                
        # Read them back to confirm
        readback = client.call("ak.wwise.core.object.get", {
            "from": {"id": [ga_guid]}
        }, options={"return": [
            "id", "@PlaylistItemType", "@PlayMode", "@LoopCount", "@NormalOrShuffle", "@Weight"
        ]})
        print("\nReadback properties after setting:")
        pprint.pprint(readback.get("return", []))
        
    finally:
        try:
            client.call("ak.wwise.core.object.delete", {"object": container_guid})
            print("Deleted container and cleaned up.")
        except Exception as e:
            print(f"Failed to clean up: {e}")
            
    client.disconnect()

if __name__ == "__main__":
    investigate()

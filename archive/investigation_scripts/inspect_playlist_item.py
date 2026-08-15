import json
import pprint
from waapi import WaapiClient

def inspect_one():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        # Get all MusicPlaylistItems first
        res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "name", "path"]})
        
        items = res.get("return", [])
        if not items:
            print("No playlist items found.")
            return
            
        target_id = items[0]["id"]
        print(f"\nInspecting item {target_id}:")
        
        # Get details of this item, specifically requesting parent, owner, and other potential relations
        details = client.call("ak.wwise.core.object.get", {
            "from": {"id": [target_id]}
        }, options={"return": [
            "id", "name", "type", "path", "parent", "owner", 
            "@PlaylistItemType", "@PlayMode", "@LoopCount", "@NormalOrShuffle", "@Weight"
        ]})
        print("\nDetails:")
        pprint.pprint(details.get("return", []))
        
        # Check references
        props = client.call("ak.wwise.core.object.getPropertyAndReferenceNames", {
            "object": target_id
        })
        print("\nProperties/References list:")
        pprint.pprint(props.get("return", []))
        
    finally:
        client.disconnect()

if __name__ == "__main__":
    inspect_one()

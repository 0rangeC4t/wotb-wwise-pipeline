import json
import pprint
from waapi import WaapiClient

def investigate():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected to WAAPI.")
    
    try:
        temp_container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "ThrowawayPlaylistContainer_Investigate2",
            "onNameConflict": "replace"
        })
        container_guid = temp_container["id"]
        print(f"Created container: {container_guid}")
        
        # Save project to see if it makes a difference
        client.call("ak.wwise.core.project.save")
        
        # Let's query container children
        res_children = client.call("ak.wwise.core.object.get", {
            "from": {"id": [container_guid]},
            "transform": [{"select": ["children"]}]
        }, options={"return": ["id", "name", "type", "path"]})
        print("\nChildren of Container:")
        pprint.pprint(res_children)
        
        # Let's query descendants of Container
        res_desc = client.call("ak.wwise.core.object.get", {
            "from": {"id": [container_guid]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "path"]})
        print("\nDescendants of Container:")
        pprint.pprint(res_desc)
        
        # Let's do getPropertyAndReferenceNames on the MusicPlaylistContainer
        props_container = client.call("ak.wwise.core.object.getPropertyAndReferenceNames", {
            "object": container_guid
        })
        print("\nContainer Properties/References:")
        pprint.pprint(props_container)
        
        # Let's see if there is any reference like "PlaylistRoot"
        ref_root = client.call("ak.wwise.core.object.get", {
            "from": {"id": [container_guid]}
        }, options={"return": ["id", "name", "type", "@PlaylistRoot"]})
        print("\nPlaylistRoot reference:")
        pprint.pprint(ref_root)
        
    finally:
        try:
            client.call("ak.wwise.core.object.delete", {"object": container_guid})
            print("Deleted container.")
            client.call("ak.wwise.core.project.save")
        except Exception as e:
            print(f"Failed to clean up: {e}")
            
    client.disconnect()

if __name__ == "__main__":
    investigate()

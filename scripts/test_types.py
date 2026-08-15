from waapi import WaapiClient
import pprint

def test():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        temp_container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "ThrowawayPlaylistContainer_TypeTest",
            "onNameConflict": "replace"
        })
        container_id = temp_container["id"]
        
        # Query ofType MusicPlaylistItem to find the root item
        playlist_items_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "name", "type", "parent"]})
        
        root_items = [pi for pi in playlist_items_res.get("return", []) if pi.get("parent", {}).get("id") == container_id]
        if not root_items:
            print("Root not found.")
            return
            
        root_guid = root_items[0]["id"]
        
        # Try setting PlaylistItemType to 1, 2, 3, 4, 5
        for t_val in range(1, 6):
            try:
                g_item = client.call("ak.wwise.core.object.create", {
                    "parent": root_guid,
                    "type": "MusicPlaylistItem",
                    "name": f"Group_Type_{t_val}",
                    "onNameConflict": "replace"
                })
                g_guid = g_item["id"]
                
                client.call("ak.wwise.core.object.setProperty", {
                    "object": g_guid,
                    "property": "PlaylistItemType",
                    "value": t_val
                })
                
                # Query back
                verify = client.call("ak.wwise.core.object.get", {
                    "from": {"id": [g_guid]}
                }, options={"return": ["id", "name", "@PlaylistItemType", "path"]})
                print(f"Setting PlaylistItemType to {t_val} -> result path: {verify['return'][0]['path']}, verified PlaylistItemType: {verify['return'][0]['@PlaylistItemType']}")
            except Exception as e:
                print(f"Setting PlaylistItemType to {t_val} failed: {e}")
                
    finally:
        try:
            client.call("ak.wwise.core.object.delete", {"object": container_id})
            print("Cleaned up.")
        except Exception as e:
            print(f"Cleanup failed: {e}")
            
    client.disconnect()

if __name__ == "__main__":
    test()

import json
import pprint
from waapi import WaapiClient

def test():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        playlist_items_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "name", "type", "parent", "path"]})
        
        print("All MusicPlaylistItem objects in project:")
        pprint.pprint(playlist_items_res.get("return", []))
        
        # Also let's query all MusicPlaylistContainer objects in the project
        containers_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistContainer"]}
        }, options={"return": ["id", "name", "type", "path"]})
        
        print("\nAll MusicPlaylistContainer objects in project:")
        pprint.pprint(containers_res.get("return", []))
        
    finally:
        client.disconnect()

if __name__ == "__main__":
    test()

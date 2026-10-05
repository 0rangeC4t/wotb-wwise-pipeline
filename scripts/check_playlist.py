from waapi import WaapiClient
import pprint

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    try:
        res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicPlaylistItem"]}
        }, options={"return": ["id", "name", "type", "parent", "owner", "path"]})
        
        playlist_items = res.get("return", [])
        print(f"Total playlist items in project: {len(playlist_items)}")
        for pi in playlist_items:
            print(f"ID: {pi['id']}, Name: {pi['name']}, Type: {pi['type']}, Parent: {pi.get('parent')}, Owner: {pi.get('owner')}, Path: {pi['path']}")
            
            # Query properties
            props = client.call("ak.wwise.core.object.get", {
                "from": {"id": [pi['id']]}
            }, options={"return": ["@PlaylistItemType", "@LoopCount", "@Weight"]})
            print("Properties:", props.get("return", []))
            
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

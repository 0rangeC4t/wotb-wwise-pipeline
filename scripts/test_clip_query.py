from waapi import WaapiClient
import pprint

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        all_clips = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicClip"]}
        }, options={"return": ["id", "name", "type", "path", "parent"]})
        print("Clips in project:")
        pprint.pprint(all_clips.get("return", [])[:5])
        
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

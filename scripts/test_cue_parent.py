from waapi import WaapiClient
import pprint

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        # Query ofType MusicCue
        all_cues = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "parent", "owner", "path"]})
        print("Cues with parent/owner info:")
        pprint.pprint(all_cues.get("return", [])[:5])
        
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

from waapi import WaapiClient
import json

try:
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("WAAPI Connected.")
    
    # Query segment
    res = client.call("ak.wwise.core.object.get", {
        "from": {"path": ["\\Interactive Music Hierarchy\\Default Work Unit\\apk_bnk\\MusicPlaylistContainer_359976450\\MusicSegment_201235529"]}
    }, options={"return": ["id", "name", "duration", "@Duration", "properties"]})
    print("Segment duration info:", json.dumps(res, indent=2))
    
    client.disconnect()
except Exception as e:
    print("Error:", e)

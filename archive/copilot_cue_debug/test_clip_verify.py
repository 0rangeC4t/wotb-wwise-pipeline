import json
from waapi import WaapiClient

def main():
    try:
        client = WaapiClient()
        print("Connected to WAAPI")
        
        res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicClip"]}
        }, options={"return": ["id", "name", "type", "path", "@EndTrimOffset", "@PlayAt"]})
        print("MusicClips:", json.dumps(res.get("return", []), indent=2))
        
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == '__main__':
    main()

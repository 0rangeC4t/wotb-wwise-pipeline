import json
from waapi import WaapiClient

def main():
    try:
        client = WaapiClient()
        print("Connected to WAAPI")
        
        # Create segment
        seg = client.call('ak.wwise.core.object.create', {
            'parent': '\\Interactive Music Hierarchy\\Default Work Unit',
            'type': 'MusicSegment',
            'name': 'TEST_SEG_CUE',
            'onNameConflict': 'replace'
        })
        print('Segment created:', seg['id'])
        client.call("ak.wwise.core.project.save")
        
        # Query ofType MusicCue
        res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "type", "path", "@TimeMs", "@CueType"]})
        
        for item in res.get("return", []):
            if "TEST_SEG_CUE" in item["path"]:
                print("Found cue for TEST_SEG_CUE:", json.dumps(item, indent=2))
                
        # Clean up
        client.call("ak.wwise.core.object.delete", {"object": seg["id"]})
        client.call("ak.wwise.core.project.save")
        print("Cleaned up.")
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == '__main__':
    main()

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
            'name': 'TEST_SEG_PROPS',
            'onNameConflict': 'replace'
        })
        print('Segment created:', seg['id'])
        
        # Get descendants of segment (the auto-created Entry and Exit cues)
        res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg['id']]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "path", "properties"]})
        print("Descendants:", json.dumps(res, indent=2))
        
        # Clean up
        client.call("ak.wwise.core.object.delete", {"object": seg["id"]})
        print("Cleaned up.")
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == '__main__':
    main()

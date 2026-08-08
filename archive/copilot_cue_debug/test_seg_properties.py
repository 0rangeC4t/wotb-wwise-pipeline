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
            'name': 'TEST_PROP_NAMES_SEG',
            'onNameConflict': 'replace'
        })
        seg_id = seg['id']
        
        # Get property names
        res = client.call("ak.wwise.core.object.getPropertyNames", {
            "object": seg_id
        })
        print("Property names of MusicSegment:", json.dumps(res, indent=2))
        
        # Clean up
        client.call("ak.wwise.core.object.delete", {"object": seg_id})
        client.call("ak.wwise.core.project.save")
        print("Cleaned up.")
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == '__main__':
    main()

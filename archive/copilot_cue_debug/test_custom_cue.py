import json
from waapi import WaapiClient

def main():
    try:
        client = WaapiClient()
        print("Connected to WAAPI")
        
        # 1. Create segment
        seg = client.call('ak.wwise.core.object.create', {
            'parent': '\\Interactive Music Hierarchy\\Default Work Unit',
            'type': 'MusicSegment',
            'name': 'TEST_SEG_CUE',
            'onNameConflict': 'replace'
        })
        print('Segment created:', seg['id'])
        
        # 2. Try to create MusicCue child
        cue = client.call('ak.wwise.core.object.create', {
            'parent': seg['id'],
            'type': 'MusicCue',
            'name': 'CustomCue',
        })
        print('Cue created:', cue['id'])
        
        # 3. Try to set TimeMs on child cue
        client.call('ak.wwise.core.object.setProperty', {
            'object': cue['id'],
            'property': 'TimeMs',
            'value': 1234.0
        })
        print('TimeMs set successfully!')
        
        # 4. Get cues under segment to see what exists
        cues_res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg['id']]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "TimeMs"]})
        print("Descendants of segment:", json.dumps(cues_res, indent=2))
        
        # Clean up
        client.call("ak.wwise.core.object.delete", {"object": seg["id"]})
        print("Cleaned up.")
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    main()

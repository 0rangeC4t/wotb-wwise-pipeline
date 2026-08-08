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
            'name': 'TEST_SEG_VERIFY',
            'onNameConflict': 'replace'
        })
        seg_id = seg['id']
        print('Segment created:', seg_id)
        client.call("ak.wwise.core.project.save")
        
        # Query ofType MusicCue
        res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "type", "path", "@TimeMs", "@CueType"]})
        
        exit_cue_id = None
        for item in res.get("return", []):
            if "TEST_SEG_VERIFY" in item["path"] and item["name"] == "Exit Cue":
                exit_cue_id = item["id"]
                print("Found Exit Cue before:", item)
                
        if exit_cue_id:
            # Let's set TimeMs
            print("Setting TimeMs to 5432.1 ms...")
            client.call("ak.wwise.core.object.setProperty", {
                "object": exit_cue_id,
                "property": "TimeMs",
                "value": 5432.1
            })
            print("setProperty called.")
            
            # Save project
            client.call("ak.wwise.core.project.save")
            
            # Read back
            res2 = client.call("ak.wwise.core.object.get", {
                "from": {"id": [exit_cue_id]}
            }, options={"return": ["id", "name", "type", "path", "@TimeMs", "@CueType"]})
            print("Found Exit Cue after:", res2.get("return", []))
            
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

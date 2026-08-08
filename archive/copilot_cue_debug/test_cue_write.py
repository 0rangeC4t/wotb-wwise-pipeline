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
            'name': 'TEST_SEG_CUE_WRITE',
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
            if "TEST_SEG_CUE_WRITE" in item["path"] and item["name"] == "Exit Cue":
                exit_cue_id = item["id"]
                print("Found Exit Cue:", item)
                
        if exit_cue_id:
            # Let's try setting TimeMs in different ways
            try:
                print("Attempt 1: Setting TimeMs as 2000.0")
                client.call("ak.wwise.core.object.setProperty", {
                    "object": exit_cue_id,
                    "property": "TimeMs",
                    "value": 2000.0
                })
                print("Attempt 1 Success!")
            except Exception as e:
                print("Attempt 1 Failed:", e)
                
            try:
                print("Attempt 2: Setting @TimeMs as 2000.0")
                client.call("ak.wwise.core.object.setProperty", {
                    "object": exit_cue_id,
                    "property": "@TimeMs",
                    "value": 2000.0
                })
                print("Attempt 2 Success!")
            except Exception as e:
                print("Attempt 2 Failed:", e)

            # Let's try setting on the parent segment?
            try:
                print("Attempt 3: Setting TimeMs on Segment")
                client.call("ak.wwise.core.object.setProperty", {
                    "object": seg_id,
                    "property": "TimeMs",
                    "value": 2000.0
                })
                print("Attempt 3 Success!")
            except Exception as e:
                print("Attempt 3 Failed:", e)
                
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

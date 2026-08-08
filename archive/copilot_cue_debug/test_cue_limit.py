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
            'name': 'TEST_LIMIT_SEG',
            'onNameConflict': 'replace'
        })
        seg_id = seg['id']
        
        # Read EndPosition
        res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_id]}
        }, options={"return": ["id", "name", "@EndPosition"]})
        print("EndPosition:", res.get("return", []))
        
        # Get Exit Cue ID
        cues_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "type", "path", "@TimeMs"]})
        
        exit_cue_id = None
        for cue in cues_res.get("return", []):
            if "TEST_LIMIT_SEG" in cue["path"] and cue["name"] == "Exit Cue":
                exit_cue_id = cue["id"]
                print("Exit cue before:", cue)
                
        # Try setting TimeMs on Exit Cue to 2000.0 ms (which is LESS than 4000.0 ms EndPosition)
        if exit_cue_id:
            try:
                print("Setting TimeMs on Exit Cue to 2000.0 ms...")
                client.call("ak.wwise.core.object.setProperty", {
                    "object": exit_cue_id,
                    "property": "TimeMs",
                    "value": 2000.0
                })
                print("Successfully set Exit Cue TimeMs to 2000.0 ms!")
            except Exception as e:
                print("Failed to set to 2000.0 ms:", e)
                
            try:
                print("Setting TimeMs on Exit Cue to 5000.0 ms...")
                client.call("ak.wwise.core.object.setProperty", {
                    "object": exit_cue_id,
                    "property": "TimeMs",
                    "value": 5000.0
                })
                print("Successfully set Exit Cue TimeMs to 5000.0 ms!")
            except Exception as e:
                print("Failed to set to 5000.0 ms:", e)
                
        client.call("ak.wwise.core.project.save")
        
        # Read back
        if exit_cue_id:
            cue_after = client.call("ak.wwise.core.object.get", {
                "from": {"id": [exit_cue_id]}
            }, options={"return": ["id", "name", "@TimeMs"]})
            print("Exit Cue after:", cue_after.get("return", []))
            
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

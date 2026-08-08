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
            'name': 'TEST_SEG_ENDPOS',
            'onNameConflict': 'replace'
        })
        seg_id = seg['id']
        print('Segment created:', seg_id)
        
        # Read EndPosition
        res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_id]}
        }, options={"return": ["id", "name", "@EndPosition"]})
        print("EndPosition before:", res.get("return", []))
        
        # Get Exit Cue ID
        cues_res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "type", "path", "@TimeMs"]})
        
        exit_cue_id = None
        for cue in cues_res.get("return", []):
            if "TEST_SEG_ENDPOS" in cue["path"] and cue["name"] == "Exit Cue":
                exit_cue_id = cue["id"]
                print("Exit cue before:", cue)
                
        # Try setting EndPosition on Segment
        print("Setting EndPosition on segment to 7680.0 ms...")
        client.call("ak.wwise.core.object.setProperty", {
            "object": seg_id,
            "property": "EndPosition",
            "value": 7680.0
        })
        print("Set EndPosition on segment successfully!")
        
        # Try setting TimeMs on Exit Cue
        if exit_cue_id:
            print("Setting TimeMs on Exit Cue to 7680.0 ms...")
            client.call("ak.wwise.core.object.setProperty", {
                "object": exit_cue_id,
                "property": "TimeMs",
                "value": 7680.0
            })
            print("Set Exit Cue TimeMs successfully!")
            
        client.call("ak.wwise.core.project.save")
        
        # Read back
        res_after = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_id]}
        }, options={"return": ["id", "name", "@EndPosition"]})
        print("EndPosition after:", res_after.get("return", []))
        
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

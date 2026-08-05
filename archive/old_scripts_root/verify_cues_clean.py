from waapi import WaapiClient
import json

try:
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("WAAPI Connected.")
    
    # Save project to ensure DB is in sync
    client.call("ak.wwise.core.project.save")
    
    # Query all MusicCue objects
    cues_res = client.call("ak.wwise.core.object.get", {
        "from": {"ofType": ["MusicCue"]}
    }, options={"return": ["id", "name", "path"]})
    
    cues = cues_res.get("return", [])
    print(f"Found {len(cues)} total cues:")
    for cue in cues:
        print(f"  Cue: {cue['name']} at {cue['path']} (ID: {cue['id']})")
        
        # Try setting TimeMs if it is Exit Cue of MusicSegment_201235529
        if "MusicSegment_201235529" in cue["path"] and cue["name"] == "Exit Cue":
            try:
                client.call("ak.wwise.core.object.setProperty", {
                    "object": cue["id"],
                    "property": "TimeMs",
                    "value": 7680.0
                })
                print("SUCCESSFULLY set TimeMs to 7680.0!")
            except Exception as e:
                print("Failed to set TimeMs:", e)
                
    client.call("ak.wwise.core.project.save")
    client.disconnect()
except Exception as e:
    print("Error:", e)

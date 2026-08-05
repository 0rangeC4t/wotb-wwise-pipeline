from waapi import WaapiClient
import json

try:
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("WAAPI Connected.")
    
    # Try setting Time to 7.68 seconds on active Exit Cue
    res = client.call("ak.wwise.core.object.setProperty", {
        "object": "{F0262028-ACBD-41E7-9063-9A36493DA6D8}",
        "property": "Time",
        "value": 7.68
    })
    print("Set property response:", json.dumps(res, indent=2))
    
    client.call("ak.wwise.core.project.save")
    print("Saved project.")
    client.disconnect()
except Exception as e:
    print("Error:", e)

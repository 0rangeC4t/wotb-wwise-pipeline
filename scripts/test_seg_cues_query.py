from waapi import WaapiClient
import pprint

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        container = client.call("ak.wwise.core.object.create", {
            "parent": "\\Interactive Music Hierarchy\\Default Work Unit",
            "type": "MusicPlaylistContainer",
            "name": "Test_Cntr_Cue_Query",
            "onNameConflict": "replace"
        })
        container_guid = container["id"]
        
        seg = client.call("ak.wwise.core.object.create", {
            "parent": container_guid,
            "type": "MusicSegment",
            "name": "Test_Seg_Cue_Query",
            "onNameConflict": "replace"
        })
        seg_guid = seg["id"]
        
        # Save project
        client.call("ak.wwise.core.project.save")
        
        # Query descendants
        desc_res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "@CueType", "path"]})
        print("Descendants:")
        pprint.pprint(desc_res.get("return", []))
        
        # Query ofType MusicCue
        all_cues = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "type", "@CueType", "path"]})
        print("All Cues in project:")
        pprint.pprint([c for c in all_cues.get("return", []) if "Test_Seg_Cue_Query" in c["path"]])
        
    finally:
        client.call("ak.wwise.core.object.delete", {"object": container_guid})
        client.call("ak.wwise.core.project.save")
        
    client.disconnect()

if __name__ == "__main__":
    main()

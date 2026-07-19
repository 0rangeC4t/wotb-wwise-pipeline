from waapi import WaapiClient
import pprint

def query_objects():
    try:
        client = WaapiClient(url="ws://localhost:8080/waapi")
        print("WAAPI connected.")
        
        args = {
            "from": {
                "path": ["\\Actor-Mixer Hierarchy"]
            },
            "transform": [
                {"select": ["descendants"]}
            ]
        }
        options = {
            "return": ["id", "name", "type", "path"]
        }
        
        result = client.call("ak.wwise.core.object.get", args, options=options)
        objects = result.get("return", [])
        
        sounds = [o for o in objects if o.get("type") == "Sound"]
        print(f"Total objects under Actor-Mixer Hierarchy: {len(objects)}")
        print(f"Total Sound objects: {len(sounds)}")
        
        folders = {}
        for obj in sounds:
            path = obj.get("path", "")
            parts = path.split("\\")
            # \Actor-Mixer Hierarchy\Default Work Unit\Folder\...
            # parts = ['', 'Actor-Mixer Hierarchy', 'Default Work Unit', 'Folder', ...]
            if len(parts) > 3:
                top_folder = parts[3]
                folders[top_folder] = folders.get(top_folder, 0) + 1
            else:
                folders["<root>"] = folders.get("<root>", 0) + 1
                
        print("Breakdown of Sound objects by top-level folder (under Default Work Unit):")
        for k, v in sorted(folders.items(), key=lambda item: item[1], reverse=True):
            print(f"  {k}: {v}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    query_objects()

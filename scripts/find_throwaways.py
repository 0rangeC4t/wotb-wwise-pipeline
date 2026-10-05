from waapi import WaapiClient

def main():
    try:
        client = WaapiClient(url="ws://localhost:8080/waapi")
        print("Connected to WAAPI.")
        
        args = {
            "from": {
                "path": ["\\Interactive Music Hierarchy"]
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
        
        print(f"Total objects under Interactive Music Hierarchy: {len(objects)}")
        
        test_objects = []
        for obj in objects:
            name = obj.get("name", "")
            if "throwaway" in name.lower() or "testbuild" in name.lower():
                test_objects.append(obj)
                
        print(f"Found {len(test_objects)} test/throwaway objects to delete:")
        for obj in test_objects:
            print(f"  - {obj['name']} ({obj['type']}) ID: {obj['id']} Path: {obj['path']}")
            
        if test_objects:
            # Delete objects
            for obj in test_objects:
                print(f"Deleting object {obj['name']}...")
                client.call("ak.wwise.core.object.delete", {"object": obj['id']})
                print(f"Successfully deleted {obj['name']}.")
            
            # Save project
            print("Saving Wwise project...")
            client.call("ak.wwise.core.project.save")
            print("Project saved successfully.")
        else:
            print("No matching test/throwaway objects to delete.")
            
        client.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

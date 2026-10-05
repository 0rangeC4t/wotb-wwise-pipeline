from waapi import WaapiClient
import json

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected to WAAPI.")
    
    leaf_ids = [
        "{534689F0-708E-4AE0-B5E0-86AA00FCF957}",
        "{FB742F3E-06FA-4369-AD65-BF866B7416B3}",
        "{C82C535C-A23B-48F4-BD35-5D6C962CDBE2}",
        "{8E49188A-760B-4D23-A83B-712E99F28543}",
        "{7384E562-71C4-48A3-BF8D-213A304DA322}",
        "{AEF3FB30-A8F4-422B-827A-067B10F7B509}"
    ]
    
    # Query properties and references of these leaf items
    res = client.call("ak.wwise.core.object.get", {
        "from": {"id": leaf_ids}
    }, options={
        "return": ["id", "name", "type", "path", "parent", "owner"]
    })
    
    print("\n--- Leaf Items Readback ---")
    print(json.dumps(res, indent=2))
    
    # Let's inspect the actual wwu file contents around one of the Leaf GUIDs to confirm the XML layout is perfect
    wwu_path = "wproj/TestProject/Interactive Music Hierarchy/Default Work Unit.wwu"
    with open(wwu_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    import re
    for leaf_id in leaf_ids:
        pattern = re.compile(rf'(<MusicPlaylistItem\s+[^>]*ID="{re.escape(leaf_id)}"[^>]*>.*?</MusicPlaylistItem>)', re.DOTALL)
        match = pattern.search(content)
        if match:
            print(f"\nXML block for {leaf_id}:")
            print(match.group(1))
        else:
            print(f"\nERROR: XML block for {leaf_id} not found!")

    client.disconnect()

if __name__ == "__main__":
    main()

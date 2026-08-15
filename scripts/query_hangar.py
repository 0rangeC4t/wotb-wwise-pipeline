from waapi import WaapiClient
import pprint

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        res = client.call("ak.wwise.core.object.get", {
            "from": {"path": ["\\Interactive Music Hierarchy\\Default Work Unit\\music_hangar"]}
        }, options={"return": ["id", "name", "type"]})
        print("Hangar folder:")
        pprint.pprint(res)
        
        if res.get("return"):
            desc = client.call("ak.wwise.core.object.get", {
                "from": {"path": ["\\Interactive Music Hierarchy\\Default Work Unit\\music_hangar"]},
                "transform": [{"select": ["descendants"]}]
            }, options={"return": ["id", "name", "type", "parent", "@EndPosition"]})
            print("Descendants:")
            for d in desc.get("return", []):
                print(f"{d['type']}: {d['name']} (ID: {d['id']}) - EndPosition: {d.get('@EndPosition')}")
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

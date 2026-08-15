from waapi import WaapiClient
import pprint

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    seg_guid = "{5D36B392-C77A-48FB-AE96-775B42CED15B}" # MusicSegment_860825692
    
    try:
        desc_res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_guid]},
            "transform": [{"select": ["descendants"]}]
        }, options={"return": ["id", "name", "type", "parent"]})
        
        for d in desc_res.get("return", []):
            print(f"Type: {d['type']}, Name: {d['name']}, ID: {d['id']}, Parent: {d.get('parent', {}).get('name')}")
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

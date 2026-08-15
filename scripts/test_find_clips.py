from waapi import WaapiClient

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    
    try:
        res = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicClip"]}
        }, options={"return": ["id", "name", "path"]})
        print("Clips in project:")
        for clip in res.get("return", []):
            if "music_hangar" in clip["path"]:
                print(f"  Clip: {clip['name']} - Path: {clip['path']}")
    except Exception as e:
        print("Error:", e)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

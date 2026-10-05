from waapi import WaapiClient

def main():
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected.")
    try:
        container_guid = "{CF2B802D-B3E4-47E0-B096-4CB36A13B52A}"
        client.call("ak.wwise.core.object.delete", {"object": container_guid})
        print("Deleted temp container.")
        client.call("ak.wwise.core.project.save")
        print("Saved project.")
    except Exception as e:
        print("Error during cleanup:", e)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

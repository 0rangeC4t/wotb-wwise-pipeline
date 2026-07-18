from waapi import WaapiClient
try:
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print(client.call("ak.wwise.core.getInfo"))
except Exception as e:
    print(f"Error connecting to WAAPI: {e}")

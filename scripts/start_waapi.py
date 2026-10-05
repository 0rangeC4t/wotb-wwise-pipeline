import os
import subprocess
import time
from waapi import WaapiClient

def main():
    print("Starting WwiseConsole waapi-server...")
    start_cmd = (
        'WINEPREFIX=$HOME/.wwise_wine wine '
        '"/home/orange_meow/.wwise_wine/drive_c/Audiokinetic/Wwise_2019.2.15.7667/Authoring/x64/Release/bin/WwiseConsole.exe" '
        'waapi-server "/mnt/data/wotb-wwise-pipeline/wproj/TestProject/TestProject.wproj" --allow-migration '
        '> wwise_waapi_attempt.log 2>&1 &'
    )
    subprocess.Popen(start_cmd, shell=True)
    
    # Wait for server to connect
    print("Waiting for WAAPI server to start...")
    connected = False
    for i in range(20):
        time.sleep(2)
        try:
            client = WaapiClient(url="ws://localhost:8080/waapi")
            print("Successfully connected to WAAPI!")
            connected = True
            client.disconnect()
            break
        except Exception:
            print("Connecting...")
            
    if not connected:
        print("Failed to connect to WAAPI.")
    else:
        print("WAAPI server is up and running.")

if __name__ == "__main__":
    main()

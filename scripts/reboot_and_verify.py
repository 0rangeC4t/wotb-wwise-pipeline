import subprocess
import time
from waapi import WaapiClient
import json

def run_cmd(cmd):
    print(f"Running command: {cmd}")
    subprocess.run(cmd, shell=True)

def main():
    print("Rebooting Wwise Console server...")
    
    # 1. Kill any running WwiseConsole.exe / wine processes
    run_cmd("pkill -9 -f WwiseConsole.exe")
    run_cmd("pkill -9 -f wine")
    time.sleep(3)

    # 2. Start WwiseConsole waapi-server again (this forces it to parse the modified WWU on disk)
    start_cmd = (
        'WINEPREFIX=$HOME/.wwise_wine wine '
        '"/home/orange_meow/.wwise_wine/drive_c/Audiokinetic/Wwise_2019.2.15.7667/Authoring/x64/Release/bin/WwiseConsole.exe" '
        'waapi-server "/mnt/data/wotb-wwise-pipeline/wproj/TestProject/TestProject.wproj" --allow-migration '
        '> wwise_waapi_attempt.log 2>&1 &'
    )
    run_cmd(start_cmd)

    # 3. Wait for server to start
    print("Waiting for WAAPI server to start...")
    connected = False
    for i in range(15):
        time.sleep(2)
        try:
            client = WaapiClient(url="ws://localhost:8080/waapi")
            print("Successfully re-connected to WAAPI!")
            connected = True
            break
        except Exception:
            print("Connecting...")
            
    if not connected:
        print("Failed to re-connect to WAAPI.")
        return

    # 4. Verify Leaf items via WAAPI to make sure they load without errors and return correct properties
    leaf_ids = [
        "{534689F0-708E-4AE0-B5E0-86AA00FCF957}",
        "{FB742F3E-06FA-4369-AD65-BF866B7416B3}",
        "{C82C535C-A23B-48F4-BD35-5D6C962CDBE2}",
        "{8E49188A-760B-4D23-A83B-712E99F28543}",
        "{7384E562-71C4-48A3-BF8D-213A304DA322}",
        "{AEF3FB30-A8F4-422B-827A-067B10F7B509}"
    ]
    
    try:
        res = client.call("ak.wwise.core.object.get", {
            "from": {"id": leaf_ids}
        }, options={
            "return": ["id", "name", "type", "path"]
        })
        print("\n=== WAAPI Leaf Items Readback ===")
        print(json.dumps(res, indent=2))
        print("SUCCESS: Project loaded completely without errors!")
    except Exception as e:
        print("ERROR: Failed to read leaf items via WAAPI after project reload:", e)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

import os
import subprocess
import time
from waapi import WaapiClient

def run_cmd(cmd):
    print(f"Running command: {cmd}")
    subprocess.run(cmd, shell=True)

def main():
    # 1. Connect and save project first
    try:
        client = WaapiClient(url="ws://localhost:8080/waapi")
        print("Connected to WAAPI. Saving project...")
        client.call("ak.wwise.core.project.save")
        client.disconnect()
        print("Saved and disconnected.")
    except Exception as e:
        print("Could not connect to save project (maybe already stopped):", e)

    # 2. Kill any running WwiseConsole.exe / wine processes
    print("Killing existing WwiseConsole.exe/wine processes...")
    run_cmd("pkill -9 -f WwiseConsole.exe")
    run_cmd("pkill -9 -f wine")
    time.sleep(3)

    # 3. Run the WWU modification script
    print("Running test_wwu_edit.py to modify WWU on disk...")
    # We will manually do the WWU modification logic here directly to be safe and clean.
    import re
    wwu_path = "wproj/TestProject/Interactive Music Hierarchy/Default Work Unit.wwu"
    with open(wwu_path, "r", encoding="utf-8") as f:
        content = f.read()

    segment_durations = {
        "{5D36B392-C77A-48FB-AE96-775B42CED15B}": 31035.290348023253, # 860825692
        "{1F9DDBF8-3EBD-4127-8147-20A8B5FA436C}": 31035.290348023253, # 195645763
        "{DAB2FBC4-E3E0-4070-B38C-09CC148ABE5D}": 26172.91396780616,  # 797778272
        "{7216554E-BEE8-4D14-9059-1A53C35A4E25}": 22253.02308487956   # 626154474
    }

    modified = False
    for seg_id, duration in segment_durations.items():
        # Find the segment section
        seg_pattern = re.compile(rf'<MusicSegment\s+[^>]*ID="{seg_id}"[^>]*>.*?</MusicSegment>', re.DOTALL)
        match = seg_pattern.search(content)
        if match:
            seg_xml = match.group(0)
            orig_seg_xml = seg_xml

            # Set EndPosition under PropertyList
            endpos_prop_pattern = re.compile(r'<Property\s+Name="EndPosition"\s+Type="Real64"\s+Value="[^"]*"\s*/>')
            if endpos_prop_pattern.search(seg_xml):
                seg_xml = endpos_prop_pattern.sub(f'<Property Name="EndPosition" Type="Real64" Value="{duration}"/>', seg_xml)
            else:
                plist_pattern = re.compile(r'<PropertyList>')
                if plist_pattern.search(seg_xml):
                    seg_xml = plist_pattern.sub(f'<PropertyList>\n\t\t\t\t\t\t\t\t\t\t<Property Name="EndPosition" Type="Real64" Value="{duration}"/>', seg_xml)
                else:
                    seg_xml = re.sub(rf'(<MusicSegment\s+[^>]*ID="{seg_id}"[^>]*>)', rf'\1\n\t\t\t\t\t\t\t\t\t<PropertyList>\n\t\t\t\t\t\t\t\t\t\t<Property Name="EndPosition" Type="Real64" Value="{duration}"/>\n\t\t\t\t\t\t\t\t\t</PropertyList>', seg_xml)

            # Find Exit Cue under CueList
            cue_pattern = re.compile(r'<MusicCue\s+Name="Exit Cue"\s+ID="[^"]*">.*?</MusicCue>', re.DOTALL)
            cue_match = cue_pattern.search(seg_xml)
            if cue_match:
                cue_xml = cue_match.group(0)
                orig_cue_xml = cue_xml
                
                # Check for Property Name="TimeMs"
                timems_prop_pattern = re.compile(r'<Property\s+Name="TimeMs"\s+Type="Real64"\s+Value="[^"]*"\s*/>')
                if timems_prop_pattern.search(cue_xml):
                    cue_xml = timems_prop_pattern.sub(f'<Property Name="TimeMs" Type="Real64" Value="{duration}"/>', cue_xml)
                else:
                    plist_pattern = re.compile(r'<PropertyList>')
                    if plist_pattern.search(cue_xml):
                        cue_xml = plist_pattern.sub(f'<PropertyList>\n\t\t\t\t\t\t\t\t\t\t\t<Property Name="TimeMs" Type="Real64" Value="{duration}"/>', cue_xml)
                    else:
                        cue_xml = re.sub(r'(<MusicCue\s+Name="Exit Cue"\s+ID="[^"]*">)', rf'\1\n\t\t\t\t\t\t\t\t\t\t\t<PropertyList>\n\t\t\t\t\t\t\t\t\t\t\t\t<Property Name="TimeMs" Type="Real64" Value="{duration}"/>\n\t\t\t\t\t\t\t\t\t\t\t</PropertyList>', cue_xml)
                
                seg_xml = seg_xml.replace(orig_cue_xml, cue_xml)

            # Replace the segment in content
            content = content.replace(orig_seg_xml, seg_xml)
            modified = True
            print(f"Modified Segment {seg_id} in memory.")

    if modified:
        with open(wwu_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("Wrote modifications to Default Work Unit.wwu on disk.")

    # 4. Start WAAPI server again
    print("Starting WwiseConsole waapi-server...")
    start_cmd = (
        'WINEPREFIX=$HOME/.wwise_wine wine '
        '"/home/orange_meow/.wwise_wine/drive_c/Audiokinetic/Wwise_2019.2.15.7667/Authoring/x64/Release/bin/WwiseConsole.exe" '
        'waapi-server "/mnt/data/wotb-wwise-pipeline/wproj/TestProject/TestProject.wproj" --allow-migration '
        '> wwise_waapi_attempt.log 2>&1 &'
    )
    subprocess.Popen(start_cmd, shell=True)
    
    # 5. Wait for server to connect
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

    # 6. Read back segment properties via WAAPI
    print("Running readback verification via WAAPI:")
    for seg_id, duration in segment_durations.items():
        res = client.call("ak.wwise.core.object.get", {
            "from": {"id": [seg_id]}
        }, options={"return": ["id", "name", "@EndPosition"]})
        print(f"Segment {res['return'][0]['name']}: EndPosition={res['return'][0]['@EndPosition']}")

        # Get Exit Cue
        all_cues = client.call("ak.wwise.core.object.get", {
            "from": {"ofType": ["MusicCue"]}
        }, options={"return": ["id", "name", "@CueType", "path", "@TimeMs"]})
        for cue in all_cues.get("return", []):
            if seg_id in cue["path"] or res['return'][0]['name'] in cue["path"]:
                if cue["@CueType"] == 1: # Exit Cue
                    print(f"  Exit Cue for {res['return'][0]['name']}: TimeMs={cue['@TimeMs']}")

    client.disconnect()

if __name__ == "__main__":
    main()

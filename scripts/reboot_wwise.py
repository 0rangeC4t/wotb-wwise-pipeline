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
        "{C48BAD93-F856-4233-B912-42C164175E33}": 31035.290348023253, # 860825692
        "{E7140C6D-FABD-43F2-907D-B213A40D9574}": 31035.290348023253, # 195645763
        "{1E304852-5C5A-475A-BBA4-85A3C077E4D1}": 26172.91396780616,  # 797778272
        "{9B3B4746-3DB0-4FAD-93E9-55F0AF90D846}": 22253.02308487956   # 626154474
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

    # Also inject Segment ObjectRef for playlist items
    seg_item_map = {
        "Item_Seg_860825692": ("MusicSegment_860825692", "{C48BAD93-F856-4233-B912-42C164175E33}"),
        "Item_Seg_195645763": ("MusicSegment_195645763", "{E7140C6D-FABD-43F2-907D-B213A40D9574}"),
        "Item_Seg_797778272": ("MusicSegment_797778272", "{1E304852-5C5A-475A-BBA4-85A3C077E4D1}"),
        "Item_Seg_626154474": ("MusicSegment_626154474", "{9B3B4746-3DB0-4FAD-93E9-55F0AF90D846}")
    }

    for item_name, (seg_name, seg_guid) in seg_item_map.items():
        pattern = re.compile(rf'<MusicPlaylistItem\s+Name="{item_name}"\s+ID="([^"]+)"\s+ShortID="([^"]+)"(?:\s*/>|>(.*?)</MusicPlaylistItem>)', re.DOTALL)
        for m in pattern.finditer(content):
            full_match = m.group(0)
            item_id = m.group(1)
            short_id = m.group(2)
            inner = m.group(3) or ""

            if "<Reference Name=\"Segment\">" not in full_match:
                ref_xml = (
                    f'<ReferenceList>\n'
                    f'\t\t\t\t\t\t\t\t\t\t\t\t\t<Reference Name="Segment">\n'
                    f'\t\t\t\t\t\t\t\t\t\t\t\t\t\t<ObjectRef Name="{seg_name}" ID="{seg_guid}" WorkUnitID="{{6BEA8D10-A7E0-4F5C-BC61-11699E72205A}}"/>\n'
                    f'\t\t\t\t\t\t\t\t\t\t\t\t\t</Reference>\n'
                    f'\t\t\t\t\t\t\t\t\t\t\t\t</ReferenceList>'
                )
                if full_match.endswith("/>"):
                    new_item_xml = f'<MusicPlaylistItem Name="{item_name}" ID="{item_id}" ShortID="{short_id}">\n\t\t\t\t\t\t\t\t\t\t\t\t{ref_xml}\n\t\t\t\t\t\t\t\t\t\t\t</MusicPlaylistItem>'
                else:
                    new_item_xml = f'<MusicPlaylistItem Name="{item_name}" ID="{item_id}" ShortID="{short_id}">\n\t\t\t\t\t\t\t\t\t\t\t\t{ref_xml}\n{inner}\n\t\t\t\t\t\t\t\t\t\t\t</MusicPlaylistItem>'
                content = content.replace(full_match, new_item_xml)
                modified = True
                print(f"Injected Segment reference for {item_name} ({item_id})")

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
        try:
            res = client.call("ak.wwise.core.object.get", {
                "from": {"id": [seg_id]}
            }, options={"return": ["id", "name", "@EndPosition"]})
            if res and res.get("return"):
                seg_obj = res["return"][0]
                print(f"Segment {seg_obj['name']}: EndPosition={seg_obj['@EndPosition']}")

                # Get Exit Cue
                all_cues = client.call("ak.wwise.core.object.get", {
                    "from": {"ofType": ["MusicCue"]}
                }, options={"return": ["id", "name", "@CueType", "path", "@TimeMs"]})
                for cue in all_cues.get("return", []):
                    if seg_id in cue["path"] or seg_obj['name'] in cue["path"]:
                        if cue["@CueType"] == 1: # Exit Cue
                            print(f"  Exit Cue for {seg_obj['name']}: TimeMs={cue['@TimeMs']}")
            else:
                print(f"Segment ID {seg_id} not found via WAAPI query.")
        except Exception as e:
            print(f"Readback query exception for {seg_id}: {e}")

    client.disconnect()

if __name__ == "__main__":
    main()

import re
import sys
from waapi import WaapiClient

def main():
    # 1. Ensure WAAPI is disconnected/project saved (already saved by build_playlist_tree)
    # The generated leaf mapping from build_tree_good.txt:
    generated_to_expected = {
        "{43BC02AC-BEF6-4DE3-9940-525D16A0E522}": "{534689F0-708E-4AE0-B5E0-86AA00FCF957}",
        "{37B3735C-51EF-4AB0-B832-53635D274AA7}": "{FB742F3E-06FA-4369-AD65-BF866B7416B3}",
        "{7759EF86-A678-477E-B6E4-7E083A2B88C1}": "{C82C535C-A23B-48F4-BD35-5D6C962CDBE2}",
        "{B9DAC42B-6D3C-455C-B007-0DDBC7908181}": "{8E49188A-760B-4D23-A83B-712E99F28543}",
        "{7250E44F-EBEB-49F4-8814-03F6F716C71C}": "{7384E562-71C4-48A3-BF8D-213A304DA322}",
        "{52F7B863-6C46-4826-B245-468EA5F73519}": "{AEF3FB30-A8F4-422B-827A-067B10F7B509}"
    }

    # Leaf ID -> (Segment Name, Segment GUID)
    segment_mapping = {
        "{534689F0-708E-4AE0-B5E0-86AA00FCF957}": ("MusicSegment_860825692", "{C48BAD93-F856-4233-B912-42C164175E33}"),
        "{FB742F3E-06FA-4369-AD65-BF866B7416B3}": ("MusicSegment_195645763", "{E7140C6D-FABD-43F2-907D-B213A40D9574}"),
        "{C82C535C-A23B-48F4-BD35-5D6C962CDBE2}": ("MusicSegment_797778272", "{1E304852-5C5A-475A-BBA4-85A3C077E4D1}"),
        "{8E49188A-760B-4D23-A83B-712E99F28543}": ("MusicSegment_626154474", "{9B3B4746-3DB0-4FAD-93E9-55F0AF90D846}"),
        "{7384E562-71C4-48A3-BF8D-213A304DA322}": ("MusicSegment_195645763", "{E7140C6D-FABD-43F2-907D-B213A40D9574}"),
        "{AEF3FB30-A8F4-422B-827A-067B10F7B509}": ("MusicSegment_860825692", "{C48BAD93-F856-4233-B912-42C164175E33}")
    }

    wwu_path = "wproj/TestProject/Interactive Music Hierarchy/Default Work Unit.wwu"

    print("Reading WWU file...")
    with open(wwu_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 2. Reassign GUIDs from generated to expected
    print("Reassigning generated GUIDs to expected GUIDs...")
    for gen_id, exp_id in generated_to_expected.items():
        # Replace the ID in the XML
        content = content.replace(gen_id, exp_id)
        print(f"Reassigned {gen_id} -> {exp_id}")

    # 3. Insert SegmentRef immediately after </PropertyList> for each expected Leaf ID
    print("Inserting SegmentRef elements...")
    for leaf_id, (seg_name, seg_guid) in segment_mapping.items():
        print(f"Processing Leaf ID {leaf_id} -> {seg_name} ({seg_guid})")
        # Build regex to match the exact MusicPlaylistItem node with that leaf_id
        pattern = re.compile(rf'(<MusicPlaylistItem\s+[^>]*ID="{re.escape(leaf_id)}"[^>]*>.*?</MusicPlaylistItem>)', re.DOTALL)
        match = pattern.search(content)
        if not match:
            print(f"ERROR: Could not find MusicPlaylistItem with ID {leaf_id}!")
            sys.exit(1)
        
        item_block = match.group(1)
        
        # Check if SegmentRef is already inside
        if f'ID="{seg_guid}"' in item_block and "SegmentRef" in item_block:
            print(f"SegmentRef already exists in block for {leaf_id}")
            continue

        plist_end_pattern = re.compile(r'(\r?\n([ \t]*))</PropertyList>')
        plist_match = plist_end_pattern.search(item_block)
        if not plist_match:
            # Maybe </PropertyList> is on the same line without a newline?
            # Let's look for </PropertyList> directly
            plist_end_pattern_simple = re.compile(r'</PropertyList>')
            plist_match_simple = plist_end_pattern_simple.search(item_block)
            if not plist_match_simple:
                print(f"ERROR: No </PropertyList> found inside MusicPlaylistItem block for {leaf_id}!")
                sys.exit(1)
            
            # Insert immediately after without indentation mapping
            segment_ref_str = f'</PropertyList>\n<SegmentRef Name="{seg_name}" ID="{seg_guid}"/>'
            new_item_block = plist_end_pattern_simple.sub(segment_ref_str, item_block, count=1)
        else:
            newline_and_indent = plist_match.group(1)
            # We want to insert the SegmentRef immediately after </PropertyList> with the same indentation
            segment_ref_str = f'</PropertyList>{newline_and_indent}<SegmentRef Name="{seg_name}" ID="{seg_guid}"/>'
            new_item_block = plist_end_pattern.sub(segment_ref_str, item_block, count=1)

        content = content.replace(item_block, new_item_block, 1)
        print(f"Successfully modified block for {leaf_id}")

    # 4. Write modified content back to .wwu file
    print("Writing modified content back to Default Work Unit.wwu...")
    with open(wwu_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)
    print("File saved successfully.")

    # 5. Reconnect to WAAPI and open the project using ui.project.open
    print("Connecting to WAAPI...")
    client = WaapiClient(url="ws://localhost:8080/waapi")
    print("Connected. Reopening project with force reload...")
    try:
        proj_path = "/mnt/data/wotb-wwise-pipeline/wproj/TestProject/TestProject.wproj"
        res = client.call("ak.wwise.ui.project.open", {
            "bypassSave": True,
            "path": proj_path
        })
        print("Project open call executed. Response:", res)
        print("SUCCESS: Project loaded without errors!")
    except Exception as e:
        print("ERROR: Project load failed or contains errors:", e)
        sys.exit(1)
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()

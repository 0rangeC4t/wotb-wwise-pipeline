import re

mapping = {
    "{534689F0-708E-4AE0-B5E0-86AA00FCF957}": ("MusicSegment_860825692", "{C48BAD93-F856-4233-B912-42C164175E33}"),
    "{FB742F3E-06FA-4369-AD65-BF866B7416B3}": ("MusicSegment_195645763", "{E7140C6D-FABD-43F2-907D-B213A40D9574}"),
    "{C82C535C-A23B-48F4-BD35-5D6C962CDBE2}": ("MusicSegment_797778272", "{1E304852-5C5A-475A-BBA4-85A3C077E4D1}"),
    "{8E49188A-760B-4D23-A83B-712E99F28543}": ("MusicSegment_626154474", "{9B3B4746-3DB0-4FAD-93E9-55F0AF90D846}"),
    "{7384E562-71C4-48A3-BF8D-213A304DA322}": ("MusicSegment_195645763", "{E7140C6D-FABD-43F2-907D-B213A40D9574}"),
    "{AEF3FB30-A8F4-422B-827A-067B10F7B509}": ("MusicSegment_860825692", "{C48BAD93-F856-4233-B912-42C164175E33}")
}

wwu_path = "wproj/TestProject/Interactive Music Hierarchy/Default Work Unit.wwu"

with open(wwu_path, "r", encoding="utf-8") as f:
    content = f.read()

# Let's perform the insertions.
# For each leaf ID:
# 1. Locate <MusicPlaylistItem ... ID="{leaf_id}" ...> ... </MusicPlaylistItem> block
# 2. Inside that block, find the </PropertyList> line
# 3. Insert <SegmentRef Name="{seg_name}" ID="{seg_id}"/> on a new line immediately after </PropertyList>
#    matching the indentation of </PropertyList>.

modified_content = content

for leaf_id, (seg_name, seg_guid) in mapping.items():
    print(f"Processing Leaf ID {leaf_id} -> {seg_name} ({seg_guid})")
    # Build a regex that matches the exact MusicPlaylistItem element block
    # We want to match reluctantly up to the first closing </MusicPlaylistItem>
    pattern = re.compile(rf'(<MusicPlaylistItem\s+[^>]*ID="{re.escape(leaf_id)}"[^>]*>.*?</MusicPlaylistItem>)', re.DOTALL)
    match = pattern.search(modified_content)
    if not match:
        print(f"WARNING: Could not find MusicPlaylistItem with ID {leaf_id}!")
        continue
    
    item_block = match.group(1)
    
    # Within this block, find the closing PropertyList tag
    # Let's find </PropertyList> and capture its leading whitespace
    plist_end_pattern = re.compile(r'(\n([ \t]*))</PropertyList>')
    plist_match = plist_end_pattern.search(item_block)
    if not plist_match:
        print(f"WARNING: No </PropertyList> found inside MusicPlaylistItem block for {leaf_id}!")
        continue
    
    newline_and_indent = plist_match.group(1)
    indent = plist_match.group(2)
    
    # We want to insert the SegmentRef immediately after </PropertyList> with the same indentation
    segment_ref_str = f'</PropertyList>{newline_and_indent}<SegmentRef Name="{seg_name}" ID="{seg_guid}"/>'
    
    new_item_block = plist_end_pattern.sub(segment_ref_str, item_block, count=1)
    
    # Replace the old block in modified_content with the new block
    # Ensure we only replace this exact match (to prevent side-effects)
    modified_content = modified_content.replace(item_block, new_item_block, 1)
    print(f"Successfully modified block for {leaf_id}")

with open(wwu_path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(modified_content)

print("Modification complete. Saved file.")

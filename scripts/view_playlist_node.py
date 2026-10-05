with open("wproj/TestProject/Interactive Music Hierarchy/Default Work Unit.wwu", "r", encoding="utf-8") as f:
    content = f.read()

import re
guid = "{534689F0-708E-4AE0-B5E0-86AA00FCF957}"
pattern = re.compile(rf'(<MusicPlaylistItem\s+[^>]*ID="{guid}"[^>]*>.*?</MusicPlaylistItem>)', re.DOTALL)
match = pattern.search(content)

with open("view_node_out.txt", "w", encoding="utf-8") as out:
    if match:
        out.write(match.group(1))
    else:
        # Let's find just the open tag and a few lines after
        tag_pat = re.compile(rf'(<MusicPlaylistItem\s+[^>]*ID="{guid}"[^>]*>)')
        match2 = tag_pat.search(content)
        if match2:
            start_pos = match2.start()
            out.write(content[start_pos:start_pos+1000])

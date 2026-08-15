with open("wproj/TestProject/Interactive Music Hierarchy/Default Work Unit.wwu", "r", encoding="utf-8") as f:
    content = f.read()

seg_idx = content.find('Name="MusicSegment_860825692"')
if seg_idx != -1:
    next_seg_idx = content.find('<MusicSegment', seg_idx + 1)
    if next_seg_idx == -1:
        next_seg_idx = len(content)
        
    segment_xml = content[seg_idx:next_seg_idx]
    
    # Let's search for MusicCue
    cue_idx = 0
    while True:
        cue_idx = segment_xml.find('<MusicCue', cue_idx)
        if cue_idx == -1:
            break
        end_cue = segment_xml.find('</MusicCue>', cue_idx)
        print(segment_xml[cue_idx:end_cue+11])
        cue_idx = end_cue + 11
else:
    print("Segment not found.")

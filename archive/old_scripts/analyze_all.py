import json

def analyze_json(json_path):
    print(f"\n==================================================")
    print(f"Analyzing {json_path}")
    print(f"==================================================")
    with open(json_path) as f:
        data = json.load(f)

    # Walk all objects
    tracks = {}
    segments = {}
    ranseqs = {}
    switches = {}

    for obj_id, objs in data.items():
        for obj in objs:
            name = obj['name']
            if name == 'CAkMusicTrack':
                tracks[obj_id] = obj
            elif name == 'CAkMusicSegment':
                segments[obj_id] = obj
            elif name == 'CAkMusicRanSeqCntr':
                ranseqs[obj_id] = obj
            elif name == 'CAkMusicSwitchCntr':
                switches[obj_id] = obj

    print(f"Stats: Tracks={len(tracks)}, Segments={len(segments)}, RanSeq={len(ranseqs)}, Switches={len(switches)}")

    # Let's extract tree relationships
    # 1. Track to Source mapping
    # 2. Segment to Track mapping
    # 3. RanSeq/Switch to Segment mapping

    print("\n--- TRACKS & SOURCES ---")
    for tid, tobj in sorted(tracks.items()):
        # Find sources
        sources = []
        parent_id = None
        
        # Helper to find fields recursively
        def walk_find_sources(node):
            nonlocal parent_id
            if node['type'] == 'field':
                if node['name'] == 'DirectParentID':
                    parent_id = node['value']
            elif node['type'] in ['object', 'list']:
                # If this object is a source, it might contain a source ID
                if node['name'] == 'AkSourceDefinition':
                    src_id = None
                    for child in node['children']:
                        if child['type'] == 'field' and child['name'] in ['id', 'ulSourceID', 'sourceID']:
                            src_id = child['value']
                    if src_id:
                        sources.append(src_id)
                for child in node['children']:
                    walk_find_sources(child)
                    
        for child in tobj['children']:
            walk_find_sources(child)
            
        print(f"Track ID {tid}: Parent Segment ID = {parent_id}, Source IDs = {sources}")

    print("\n--- SEGMENTS ---")
    for sid, sobj in sorted(segments.items()):
        duration = None
        num_markers = 0
        markers_info = []
        child_ids = []
        parent_id = None
        
        def walk_segment(node):
            nonlocal duration, num_markers, parent_id
            if node['type'] == 'field':
                if node['name'] == 'fDuration':
                    duration = node['value']
                elif node['name'] == 'ulNumMarkers':
                    num_markers = node['value']
                elif node['name'] == 'DirectParentID':
                    parent_id = node['value']
                elif node['name'] == 'ulChildID':
                    child_ids.append(node['value'])
            elif node['type'] == 'object' and node['name'] == 'AkMusicMarkerWwise':
                m_id = None
                m_pos = None
                m_name = ""
                for child in node['children']:
                    if child['type'] == 'field':
                        if child['name'] == 'id':
                            m_id = child['value']
                        elif child['name'] == 'fPosition':
                            m_pos = child['value']
                        elif child['name'] == 'pString':
                            m_name = child['value']
                markers_info.append({'id': m_id, 'pos': m_pos, 'name': m_name})
            elif node['type'] in ['object', 'list']:
                for child in node['children']:
                    walk_segment(child)
                    
        for child in sobj['children']:
            walk_segment(child)
            
        print(f"Segment ID {sid}: Parent Container = {parent_id}, Children Tracks = {child_ids}, Duration = {duration}")
        for m in markers_info:
            print(f"  Marker: ID={m['id']}, Pos={m['pos']}ms, Name='{m['name']}'")

    print("\n--- RANSEQ CONTAINERS ---")
    for rid, robj in sorted(ranseqs.items()):
        child_ids = []
        playlist_items = []
        parent_id = None
        
        def walk_ranseq(node):
            nonlocal parent_id
            if node['type'] == 'field':
                if node['name'] == 'DirectParentID':
                    parent_id = node['value']
                elif node['name'] == 'ulChildID':
                    child_ids.append(node['value'])
                elif node['name'] == 'SegmentID' and node['value'] != '0':
                    playlist_items.append(node['value'])
            elif node['type'] in ['object', 'list']:
                for child in node['children']:
                    walk_ranseq(child)
                    
        for child in robj['children']:
            walk_ranseq(child)
            
        print(f"RanSeq ID {rid}: Parent Container = {parent_id}, Children = {child_ids}, Playlist Segments = {playlist_items}")

    print("\n--- SWITCH CONTAINERS ---")
    for swid, swobj in sorted(switches.items()):
        child_ids = []
        parent_id = None
        group_id = None
        group_type = None
        default_state = None
        
        def walk_switch(node):
            nonlocal parent_id, group_id, group_type, default_state
            if node['type'] == 'field':
                if node['name'] == 'DirectParentID':
                    parent_id = node['value']
                elif node['name'] == 'ulChildID':
                    child_ids.append(node['value'])
                elif node['name'] == 'ulGroupVal':
                    # Switch group/State group ID
                    group_id = node['value']
                elif node['name'] == 'eGroupType':
                    group_type = node['value'] # 0 = State, 1 = Switch?
                elif node['name'] == 'ulDefaultSwitchVal':
                    default_state = node['value']
            elif node['type'] in ['object', 'list']:
                for child in node['children']:
                    walk_switch(child)
                    
        for child in swobj['children']:
            walk_switch(child)
            
        print(f"Switch ID {swid}: Parent Container = {parent_id}, GroupID = {group_id} (Type {group_type}), DefaultState = {default_state}, Children = {child_ids}")

analyze_json('apk_music.json')
analyze_json('music_hangar_music.json')

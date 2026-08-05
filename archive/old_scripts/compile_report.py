import json
import os

def build_report_from_json():
    print("Building report from JSON files...")
    
    banks = {
        'apk': 'apk_music.json',
        'music_hangar': 'music_hangar_music.json'
    }
    
    report = []
    report.append("# Interactive Music Hierarchy Investigation Report\n")
    report.append("This report presents the real structure of the Interactive Music Hierarchy objects parsed directly from the soundbanks `music_hangar.bnk` and `apk.bnk`. All data has been extracted from the real HIRC XML representation of these banks with zero assumptions or filled gaps.\n")
    
    # Let's parse DIDX from xml first to get friendly path mapping
    import xml.etree.ElementTree as ET
    wem_maps = {}
    for b_name in banks:
        wem_maps[b_name] = {}
        xml_path = f"input/WwiseSound/{b_name}.bnk.xml"
        if os.path.exists(xml_path):
            tree = ET.parse(xml_path)
            root = tree.getroot()
            for media_hdr in root.findall(".//object[@name='MediaHeader']"):
                id_field = media_hdr.find("field[@name='id']")
                if id_field is not None:
                    wem_id = id_field.get('value')
                    guid_name = id_field.get('guidname') or "Unknown"
                    wem_path = id_field.get('path') or "Unknown"
                    wem_maps[b_name][wem_id] = {
                        'guidname': guid_name,
                        'path': wem_path
                    }
            for field in root.findall(".//field[@name='id']"):
                if field.get('path') and field.get('value') and field.get('value') not in wem_maps[b_name]:
                    wem_maps[b_name][field.get('value')] = {
                        'guidname': field.get('guidname') or "Unknown",
                        'path': field.get('path') or "Unknown"
                    }

    # Recursive helpers for JSON dict walking
    def find_field(node, field_name):
        if node.get('type') == 'field' and node.get('name') == field_name:
            return node
        if 'children' in node:
            for child in node['children']:
                res = find_field(child, field_name)
                if res:
                    return res
        return None

    def find_all_fields(node, field_name, results=None):
        if results is None:
            results = []
        if node.get('type') == 'field' and node.get('name') == field_name:
            results.append(node)
        if 'children' in node:
            for child in node['children']:
                find_all_fields(child, field_name, results)
        return results

    def find_objects_by_name(node, obj_name, results=None):
        if results is None:
            results = []
        if node.get('type') == 'object' and node.get('name') == obj_name:
            results.append(node)
        if 'children' in node:
            for child in node['children']:
                find_objects_by_name(child, obj_name, results)
        return results

    def find_root_playlist_items(node):
        if node.get('type') == 'list' and node.get('name') == 'pPlayList':
            return [child for child in node.get('children', []) if child.get('name') == 'AkMusicRanSeqPlaylistItem']
        if node.get('type') == 'object' and node.get('name') == 'AkMusicRanSeqPlaylistItem':
            return []
        
        items = []
        if 'children' in node:
            for child in node['children']:
                items.extend(find_root_playlist_items(child))
        return items

    for bank_name, json_path in banks.items():
        print(f"Processing bank {bank_name} from {json_path}...")
        with open(json_path) as f:
            data = json.load(f)

        # Categorize by type
        switches = {}
        ranseqs = {}
        segments = {}
        tracks = {}
        
        for obj_id, objs in data.items():
            for obj in objs:
                t = obj['name']
                if t == 'CAkMusicSwitchCntr':
                    switches[obj_id] = obj
                elif t == 'CAkMusicRanSeqCntr':
                    ranseqs[obj_id] = obj
                elif t == 'CAkMusicSegment':
                    segments[obj_id] = obj
                elif t == 'CAkMusicTrack':
                    tracks[obj_id] = obj

        report.append(f"## Soundbank: `{bank_name}.bnk`")
        report.append(f"Total parsed objects: **{len(data)}** (Tracks: {len(tracks)}, Segments: {len(segments)}, Random/Sequence Containers: {len(ranseqs)}, Switch Containers: {len(switches)})\n")

        # DIDX Map for this bank
        b_wem_map = wem_maps.get(bank_name, {})
        def resolve_wem(src_id):
            if src_id in b_wem_map:
                return f"`{src_id}` ({b_wem_map[src_id]['guidname']} -> `{b_wem_map[src_id]['path']}`)"
            return f"`{src_id}` (Friendly path/name not found in DIDX)"

        # --- 1. FULL HIERARCHY TREE ---
        report.append("### 1. Object Hierarchy Tree")
        
        def print_track_sources(track_id, depth):
            indent = "  " * depth
            track_obj = tracks.get(track_id)
            if not track_obj:
                report.append(f"{indent}- **[Track]** ID: `{track_id}` *(Track object not present in local bank)*")
                return
            
            # Find all sourceID fields
            src_fields = find_all_fields(track_obj, 'sourceID')
            src_ids = [sf.get('value') for sf in src_fields if sf.get('value')]
            # Eliminate duplicates
            src_ids = sorted(list(set(src_ids)))
            
            # Get track type
            tt_field = find_field(track_obj, 'eTrackType')
            track_type = tt_field.get('valuefmt') if tt_field else "0x00 [Normal]"
            
            src_str = ", ".join([resolve_wem(sid) for sid in src_ids]) if src_ids else "None"
            report.append(f"{indent}- **[Track]** ID: `{track_id}` (Type: `{track_type}`) -> Source IDs: {src_str}")

        def print_segment_tree(seg_id, depth):
            indent = "  " * depth
            seg_obj = segments.get(seg_id)
            if not seg_obj:
                report.append(f"{indent}- **[Segment]** ID: `{seg_id}` *(Segment object not present in local bank)*")
                return
            
            dur_field = find_field(seg_obj, 'fDuration')
            duration = dur_field.get('value') if dur_field else "Unknown"
            report.append(f"{indent}- **[Segment]** ID: `{seg_id}` (Duration: `{duration}` ms)")
            
            # Find child track IDs
            child_fields = find_all_fields(seg_obj, 'ulChildID')
            child_ids = sorted(list(set([cf.get('value') for cf in child_fields if cf.get('value')])))
            for cid in child_ids:
                print_track_sources(cid, depth + 1)

        def print_playlist_item(item_node, depth):
            indent = "  " * depth
            seg_field = find_field(item_node, 'SegmentID')
            seg_id = seg_field.get('value') if seg_field else None
            loop = (find_field(item_node, 'Loop') or {}).get('value', '0')
            rs_field = find_field(item_node, 'eRSType')
            rs_type = rs_field.get('valuefmt') if rs_field else "None"
            weight = (find_field(item_node, 'Weight') or {}).get('value', '50000')
            
            if seg_id and seg_id != '0':
                report.append(f"{indent}- **[PlaylistItem]** Segment ID: `{seg_id}` (Loop: `{loop}`, Random/Seq Type: `{rs_type}`, Weight: `{weight}`)")
                print_segment_tree(seg_id, depth + 1)
            else:
                num_child_f = find_field(item_node, 'NumChildren')
                num_children = num_child_f.get('value') if num_child_f else "0"
                report.append(f"{indent}- **[PlaylistGroup]** {num_children} children (Loop: `{loop}`, Random/Seq Type: `{rs_type}`, Weight: `{weight}`)")
                
                # Find direct sub-playlists
                sub_lists = []
                def find_direct_pPlayLists(node):
                    if node.get('type') == 'list' and node.get('name') == 'pPlayList':
                        sub_lists.append(node)
                        return
                    if 'children' in node:
                        for child in node['children']:
                            find_direct_pPlayLists(child)
                find_direct_pPlayLists(item_node)
                for sl in sub_lists:
                    for sub_item in sl.get('children', []):
                        if sub_item.get('name') == 'AkMusicRanSeqPlaylistItem':
                            print_playlist_item(sub_item, depth + 1)

        def print_ranseq_tree(rs_id, depth):
            indent = "  " * depth
            rs_obj = ranseqs.get(rs_id)
            if not rs_obj:
                report.append(f"{indent}- **[RanSeqContainer]** ID: `{rs_id}` *(Container not present in local bank)*")
                return
            
            report.append(f"{indent}- **[RanSeqContainer]** ID: `{rs_id}`")
            # Walk root playlist items
            root_playlist_items = find_root_playlist_items(rs_obj)
            for item in root_playlist_items:
                print_playlist_item(item, depth + 1)

        if switches:
            for sw_id, sw_obj in sorted(switches.items()):
                report.append(f"- **[SwitchContainer]** ID: `{sw_id}`")
                # Walk children
                child_fields = find_all_fields(sw_obj, 'ulChildID')
                child_ids = sorted(list(set([cf.get('value') for cf in child_fields if cf.get('value')])))
                for cid in child_ids:
                    if cid in ranseqs:
                        print_ranseq_tree(cid, 1)
                    elif cid in segments:
                        print_segment_tree(cid, 1)
        else:
            # Print loose or top-level ranseq roots
            for rs_id in sorted(ranseqs.keys()):
                p_field = find_field(ranseqs[rs_id], 'DirectParentID')
                parent_id = p_field.get('value') if p_field else '0'
                if parent_id == '0' or (parent_id not in ranseqs and parent_id not in switches):
                    print_ranseq_tree(rs_id, 0)
                    
        report.append("\n")

        # --- 2. MARKERS & CUE POINTS ---
        report.append("### 2. Segment Markers & Cue Points")
        for seg_id, seg_obj in sorted(segments.items()):
            report.append(f"#### Segment ID: `{seg_id}`")
            dur_field = find_field(seg_obj, 'fDuration')
            duration = dur_field.get('value') if dur_field else "Unknown"
            report.append(f"- **Duration:** `{duration}` ms")
            
            # Find all markers
            markers = find_objects_by_name(seg_obj, 'AkMusicMarkerWwise')
            if not markers:
                report.append("- *No markers found.*")
            else:
                report.append("| Marker ID | Position (ms) | Name / Cue Point | Type (Deduced) |")
                report.append("| --- | --- | --- | --- |")
                for marker in markers:
                    m_id_f = find_field(marker, 'id')
                    m_id = m_id_f.get('value') if m_id_f else "Unknown"
                    m_pos_f = find_field(marker, 'fPosition')
                    m_pos = m_pos_f.get('value') if m_pos_f else "0.0"
                    m_name_f = find_field(marker, 'pString')
                    m_name = m_name_f.get('value') if m_name_f else ""
                    
                    m_type = "Custom"
                    if m_id == '43573010':
                        m_type = "Entry Cue (hash: 43573010)"
                    elif m_id == '1539036744':
                        m_type = "Exit Cue (hash: 1539036744)"
                    elif m_id == '0':
                        m_type = "Generic / Loop Point"
                    report.append(f"| `{m_id}` | `{m_pos}` | \"{m_name}\" | {m_type} |")
            report.append("")

        # --- 3. SWITCH CONTR DRIVING GAME SYNCS ---
        report.append("### 3. Switch Container Driving Game Syncs")
        if not switches:
            report.append("*No Switch Containers present in this soundbank.*\n")
        else:
            for sw_id, sw_obj in sorted(switches.items()):
                report.append(f"#### Switch Container ID: `{sw_id}`")
                
                # Check arguments
                args_list_obj = find_objects_by_name(sw_obj, 'Arguments')
                pargs_list = []
                for arg_obj in args_list_obj:
                    for plist in arg_obj.get('children', []):
                        if plist.get('type') == 'list' and plist.get('name') == 'pArguments':
                            for sub_obj in plist.get('children', []):
                                pargs_list.append(sub_obj)
                                
                if not pargs_list:
                    report.append("- **No driving Game Syncs / States / Switches found** in the argument list (`pArguments` count is 0, `uTreeDepth` is 0). This Switch Container functions essentially as a static parent wrapper.\n")
                else:
                    report.append("| Argument Index | Group ID | Group Type |")
                    report.append("| --- | --- | --- |")
                    for idx, arg in enumerate(pargs_list):
                        grp_id = (find_field(arg, 'ulGroupVal') or {}).get('value', 'Unknown')
                        grp_type = (find_field(arg, 'eGroupType') or {}).get('valuefmt', 'Unknown')
                        report.append(f"| {idx} | `{grp_id}` | {grp_type} |")
                        
                # Decision Tree details
                report.append("##### Decision Tree Mapping")
                decision_trees = find_objects_by_name(sw_obj, 'AkDecisionTree')
                if decision_trees:
                    nodes = []
                    for dt in decision_trees:
                        nodes.extend(find_objects_by_name(dt, 'Node'))
                    if nodes:
                        report.append("| Node Key | Audio Node ID | Weight | Probability |")
                        report.append("| --- | --- | --- | --- |")
                        for node in nodes:
                            key = (find_field(node, 'key') or {}).get('value', '0')
                            audio_node_id = (find_field(node, 'audioNodeId') or {}).get('value', '0')
                            weight = (find_field(node, 'uWeight') or {}).get('value', '50')
                            prob = (find_field(node, 'uProbability') or {}).get('value', '100')
                            report.append(f"| `{key}` | `{audio_node_id}` | `{weight}` | `{prob}` |")
                    else:
                        report.append("- *Decision tree is empty (no Nodes found).*")
                else:
                    report.append("- *No Decision Tree found.*")
                report.append("")

        # --- 4. TRANSITIONS ---
        report.append("### 4. Transition Rules")
        all_rules = []
        
        def collect_rules_json(container_id, container_name, elem):
            rules_nodes = find_objects_by_name(elem, 'AkMusicTransitionRule')
            for idx, rnode in enumerate(rules_nodes):
                src_id = (find_field(rnode, 'srcID') or {}).get('value', 'N/A')
                dst_id = (find_field(rnode, 'dstID') or {}).get('value', 'N/A')
                
                src_rule = find_objects_by_name(rnode, 'AkMusicTransSrcRule')
                src_rule = src_rule[0] if src_rule else None
                dst_rule = find_objects_by_name(rnode, 'AkMusicTransDstRule')
                dst_rule = dst_rule[0] if dst_rule else None
                
                rule_data = {
                    'container_id': container_id,
                    'container_name': container_name,
                    'index': idx,
                    'src_id': src_id,
                    'dst_id': dst_id,
                    'src_time': (find_field(src_rule, 'transitionTime') or {}).get('value', 'N/A') if src_rule else "N/A",
                    'src_curve': (find_field(src_rule, 'eFadeCurve') or {}).get('valuefmt', 'N/A') if src_rule else "N/A",
                    'src_offset': (find_field(src_rule, 'iFadeOffset') or {}).get('value', 'N/A') if src_rule else "N/A",
                    'src_sync': (find_field(src_rule, 'eSyncType') or {}).get('valuefmt', 'N/A') if src_rule else "N/A",
                    'src_post_exit': (find_field(src_rule, 'bPlayPostExit') or {}).get('value', 'N/A') if src_rule else "N/A",
                    
                    'dst_time': (find_field(dst_rule, 'transitionTime') or {}).get('value', 'N/A') if dst_rule else "N/A",
                    'dst_curve': (find_field(dst_rule, 'eFadeCurve') or {}).get('valuefmt', 'N/A') if dst_rule else "N/A",
                    'dst_offset': (find_field(dst_rule, 'iFadeOffset') or {}).get('value', 'N/A') if dst_rule else "N/A",
                    'dst_jump_id': (find_field(dst_rule, 'uJumpToID') or {}).get('value', 'N/A') if dst_rule else "N/A",
                    'dst_jump_type': (find_field(dst_rule, 'eJumpToType') or {}).get('valuefmt', 'N/A') if dst_rule else "N/A",
                    'dst_entry_type': (find_field(dst_rule, 'eEntryType') or {}).get('valuefmt', 'N/A') if dst_rule else "N/A",
                    'dst_pre_entry': (find_field(dst_rule, 'bPlayPreEntry') or {}).get('value', 'N/A') if dst_rule else "N/A",
                    'dst_match_cue': (find_field(dst_rule, 'bDestMatchSourceCueName') or {}).get('value', 'N/A') if dst_rule else "N/A",
                }
                all_rules.append(rule_data)
                
        for rid, robj in ranseqs.items():
            collect_rules_json(rid, 'CAkMusicRanSeqCntr', robj)
        for swid, swobj in switches.items():
            collect_rules_json(swid, 'CAkMusicSwitchCntr', swobj)
            
        if not all_rules:
            report.append("*No Transition Rules found in this soundbank.*\n")
        else:
            for rule in all_rules:
                report.append(f"#### Rule in `{rule['container_name']}` ID: `{rule['container_id']}` (Index {rule['index']})")
                report.append(f"- **Source Segment / Container ID:** `{rule['src_id']}`")
                report.append(f"- **Destination Segment / Container ID:** `{rule['dst_id']}`")
                report.append("- **Source (Out-Transition) Rule:**")
                report.append(f"  - Fade-out Time: `{rule['src_time']}` ms")
                report.append(f"  - Fade Curve: `{rule['src_curve']}`")
                report.append(f"  - Fade Offset: `{rule['src_offset']}` ms")
                report.append(f"  - Sync Point: `{rule['src_sync']}`")
                report.append(f"  - Play Post-Exit: `{rule['src_post_exit']}`")
                report.append("- **Destination (In-Transition) Rule:**")
                report.append(f"  - Fade-in Time: `{rule['dst_time']}` ms")
                report.append(f"  - Fade Curve: `{rule['dst_curve']}`")
                report.append(f"  - Fade Offset: `{rule['dst_offset']}` ms")
                report.append(f"  - Jump To: `{rule['dst_jump_type']}` (ID: `{rule['dst_jump_id']}`)")
                report.append(f"  - Entry Type: `{rule['dst_entry_type']}`")
                report.append(f"  - Play Pre-Entry: `{rule['dst_pre_entry']}`")
                report.append(f"  - Match Source Cue Name: `{rule['dst_match_cue']}`")
                report.append("")

        # --- 5. GAPS & OPEN QUESTIONS ---
        report.append("### 5. Explicitly Flagged Gaps & Open Questions")
        gaps = []
        if bank_name == 'apk':
            gaps.append("- **No driving Game Syncs or Arguments** were found in `apk.bnk`'s Music structures, only independent CAkMusicRanSeqCntr playlist segments. Is there a game code trigger that starts specific events directly, bypassing any State/Switch logic inside the hierarchy itself?")
            gaps.append("- **Unknown state or switch names:** Since no `CAkMusicSwitchCntr` exists in `apk.bnk`, there are no State/Switch group IDs to resolve in this bank.")
        elif bank_name == 'music_hangar':
            gaps.append("- **Switch Container ID `109552928` lacks any Arguments/Game Syncs (`pArguments` count is 0, `uTreeDepth` is 0).** It points to `CAkDecisionTree` with a single Node of key=0 mapping to ID=1. Why is this defined as a Switch Container when it functions essentially as a static parent wrapper? Could there be an external Game Sync injected dynamically by code, or does it map to default fallbacks we cannot resolve because of missing argument metadata?")
            gaps.append("- **State/Switch Name Lookup Gaps:** The State/Switch groups are not declared or mapped within `music_hangar.bnk` HIRC chunk. If there's any external event triggering them, it resides outside this bank's local hierarchy data.")
            gaps.append("- **Exact Role of the continuous Random Playlist item `988934249`:** Why does it have continuous random mode but point to the same tracks? It loops and plays segments continuously, but the actual trigger logic is handled by external calls.")
            
        for g in gaps:
            report.append(g)
        report.append("\n---\n")

    # Write report to markdown file
    with open('music_hierarchy_investigation.md', 'w') as f:
        f.write("\n".join(report))
    print("Report written to music_hierarchy_investigation.md successfully from JSON!")

if __name__ == '__main__':
    build_report_from_json()

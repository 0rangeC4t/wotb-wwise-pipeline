import xml.etree.ElementTree as ET
import json

def obj_to_dict(elem):
    res = {}
    if elem.tag == 'object':
        res['_type'] = 'object'
        res['name'] = elem.get('name')
        if elem.get('index'):
            res['index'] = elem.get('index')
    elif elem.tag == 'list':
        res['_type'] = 'list'
        res['name'] = elem.get('name')
        res['count'] = elem.get('count')
    elif elem.tag == 'field':
        res['_type'] = 'field'
        res['name'] = elem.get('name')
        if elem.get('value'):
            res['value'] = elem.get('value')
        if elem.get('valuefmt'):
            res['valuefmt'] = elem.get('valuefmt')
        if elem.get('hashname'):
            res['hashname'] = elem.get('hashname')
        if elem.get('guidname'):
            res['guidname'] = elem.get('guidname')
        if elem.get('path'):
            res['path'] = elem.get('path')
        return res

    children = []
    for child in elem:
        cd = obj_to_dict(child)
        if cd:
            children.append(cd)
    if children:
        res['children'] = children
    return res

def inspect_bank_details(xml_path):
    print(f"=== Inspecting Details {xml_path} ===")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    types_seen = {}
    for obj in root.findall('.//object'):
        obj_name = obj.get('name')
        if obj_name in ['CAkMusicSegment', 'CAkMusicTrack', 'CAkMusicRanSeqCntr', 'CAkMusicSwitchCntr']:
            if obj_name not in types_seen:
                types_seen[obj_name] = obj
                
    for t, obj in types_seen.items():
        print(f"\n=================== TYPE: {t} ===================")
        d = obj_to_dict(obj)
        print(json.dumps(d, indent=2))

inspect_bank_details('input/WwiseSound/apk.bnk.xml')
# Also inspect a SwitchCntr from music_hangar if there isn't one in apk
tree = ET.parse('input/WwiseSound/music_hangar.bnk.xml')
for obj in tree.getroot().findall('.//object'):
    if obj.get('name') == 'CAkMusicSwitchCntr':
        print(f"\n=================== TYPE: CAkMusicSwitchCntr (from music_hangar) ===================")
        print(json.dumps(obj_to_dict(obj), indent=2))
        break

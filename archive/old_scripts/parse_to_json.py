import xml.etree.ElementTree as ET
import json
import os

def parse_bnk_xml(xml_path, output_json_path):
    print(f"Parsing {xml_path}...")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Map to store all objects of interest
    objects_map = {}
    
    # Helper to recursively get all fields and sub-objects as a dict
    def parse_element(elem):
        if elem.tag == 'field':
            res = {
                'type': 'field',
                'name': elem.get('name'),
                'value': elem.get('value'),
                'valuefmt': elem.get('valuefmt')
            }
            if elem.get('hashname'):
                res['hashname'] = elem.get('hashname')
            if elem.get('guidname'):
                res['guidname'] = elem.get('guidname')
            if elem.get('path'):
                res['path'] = elem.get('path')
            return res
        elif elem.tag == 'object':
            res = {
                'type': 'object',
                'name': elem.get('name'),
                'index': elem.get('index'),
                'children': []
            }
            for child in elem:
                parsed = parse_element(child)
                if parsed:
                    res['children'].append(parsed)
            return res
        elif elem.tag == 'list':
            res = {
                'type': 'list',
                'name': elem.get('name'),
                'count': elem.get('count'),
                'children': []
            }
            for child in elem:
                parsed = parse_element(child)
                if parsed:
                    res['children'].append(parsed)
            return res
        return None

    # Find the HIRC block
    for obj in root.findall('.//object'):
        obj_name = obj.get('name')
        if obj_name in ['CAkMusicSegment', 'CAkMusicTrack', 'CAkMusicRanSeqCntr', 'CAkMusicSwitchCntr']:
            # Find the ID
            id_field = obj.find("./field[@name='ulID']")
            if id_field is None:
                # Some might have 'id' instead of 'ulID'
                id_field = obj.find("./field[@name='id']")
            
            obj_id = id_field.get('value') if id_field is not None else "unknown"
            
            parsed_obj = parse_element(obj)
            if parsed_obj:
                parsed_obj['id'] = obj_id
                if obj_id not in objects_map:
                    objects_map[obj_id] = []
                objects_map[obj_id].append(parsed_obj)

    with open(output_json_path, 'w') as f:
        json.dump(objects_map, f, indent=2)
    print(f"Saved {len(objects_map)} objects to {output_json_path}")

parse_bnk_xml('input/WwiseSound/apk.bnk.xml', 'apk_music.json')
parse_bnk_xml('input/WwiseSound/music_hangar.bnk.xml', 'music_hangar_music.json')

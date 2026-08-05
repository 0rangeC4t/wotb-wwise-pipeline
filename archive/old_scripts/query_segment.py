import json

with open('apk_music.json') as f:
    data = json.load(f)

def dump_struct(elem, depth=0):
    indent = "  " * depth
    if elem['type'] == 'field':
        print(f"{indent}Field: {elem['name']} = {elem.get('value')} ({elem.get('valuefmt') or ''})")
    elif elem['type'] == 'object':
        print(f"{indent}Object: {elem['name']}")
        for child in elem['children']:
            dump_struct(child, depth+1)
    elif elem['type'] == 'list':
        print(f"{indent}List: {elem['name']} (count={elem.get('count')})")
        for child in elem['children']:
            dump_struct(child, depth+1)

# Find any CAkMusicSegment
for obj_id, objs in data.items():
    for obj in objs:
        if obj['name'] == 'CAkMusicSegment':
            print("=== CAkMusicSegment Detail ===")
            print("ID:", obj_id)
            for child in obj['children']:
                dump_struct(child)
            break
    else:
        continue
    break

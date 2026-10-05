import json

def dump_obj(obj, indent=0):
    res = []
    if isinstance(obj, dict):
        name = obj.get('name', '')
        type_ = obj.get('type', '')
        val = obj.get('value', '')
        valfmt = obj.get('valuefmt', '')
        if name or type_ or val:
            res.append('  ' * indent + f'{type_} {name} = {val} ({valfmt})')
        for child in obj.get('children', []):
            res.extend(dump_obj(child, indent + 1))
    elif isinstance(obj, list):
        for item in obj:
            res.extend(dump_obj(item, indent))
    return res

data = json.load(open('archive/investigation_temp/music_hangar_music.json'))

print('=== 1054648317 ===')
for line in dump_obj(data.get('1054648317', [])):
    if any(k in line for k in ['DirectParentID', 'OverrideBusId', 'MakeUpGain', 'Tempo', 'Meter', 'bIsShuffle', 'uTimeSigNumBeatsBar', 'fTempo', 'fGridPeriod', 'bMeterInfoFlag']):
        print(line)

print('=== 109552928 ===')
for line in dump_obj(data.get('109552928', [])):
    if any(k in line for k in ['DirectParentID', 'OverrideBusId', 'MakeUpGain', 'Tempo', 'Meter', 'bIsShuffle', 'uTimeSigNumBeatsBar', 'fTempo', 'fGridPeriod', 'bMeterInfoFlag']):
        print(line)

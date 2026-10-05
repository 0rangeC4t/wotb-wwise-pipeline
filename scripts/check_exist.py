import os
wwu_path = 'wproj/TestProject/Interactive Music Hierarchy/Default Work Unit.wwu'
if os.path.exists(wwu_path):
    with open(wwu_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print('MusicPlaylistContainer_1054648317 exists:', 'MusicPlaylistContainer_1054648317' in content)
    print('109552928 exists:', '109552928' in content)
else:
    print('WWU not found')

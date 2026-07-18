import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../core'))

from index_parser import parse_didx
from carve_core import carve_by_index

def test_carve_bnk():
    bnk_path = os.path.join(os.path.dirname(__file__), '../input/WwiseSound/en/voiceover_crew.bnk')
    assert os.path.exists(bnk_path), f"BNK file not found: {bnk_path}"
    
    index = parse_didx(bnk_path)
    assert len(index) == 160, f"Expected 160 files in index, got {len(index)}"
    
    carved = carve_by_index(bnk_path, index)
    assert len(carved) == 160, f"Expected 160 carved files, got {len(carved)}"
    
    # Check that all carved files start with RIFF or RIFX magic
    for fid, data in carved.items():
        magic = data[:4]
        assert magic in (b'RIFF', b'RIFX'), f"File {fid} has invalid magic: {magic}"
        
    print("test_carve_bnk: SUCCESS (160/160 carved with correct RIFF/RIFX magic)")

if __name__ == '__main__':
    test_carve_bnk()

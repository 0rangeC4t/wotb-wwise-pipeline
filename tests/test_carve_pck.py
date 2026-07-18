import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../core'))

from index_parser import parse_akpk
from carve_core import carve_by_index

def test_carve_pck():
    pck_path = os.path.join(os.path.dirname(__file__), '../input/WwiseSound/weapon_basic.pck')
    assert os.path.exists(pck_path), f"PCK file not found: {pck_path}"
    
    index = parse_akpk(pck_path)
    assert len(index) == 78, f"Expected 78 files in index, got {len(index)}"
    
    carved = carve_by_index(pck_path, index)
    assert len(carved) == 78, f"Expected 78 carved files, got {len(carved)}"
    
    # Check that all carved files start with RIFF or RIFX magic
    for fid, data in carved.items():
        magic = data[:4]
        assert magic in (b'RIFF', b'RIFX'), f"File {fid} has invalid magic: {magic}"
        
    print("test_carve_pck: SUCCESS (78/78 carved with correct RIFF/RIFX magic)")

if __name__ == '__main__':
    test_carve_pck()

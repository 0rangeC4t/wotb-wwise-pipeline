import mmap
import os

def carve_by_index(filepath, index_table):
    results = {}
    if not index_table:
        return results
        
    with open(filepath, 'rb') as f:
        size = os.path.getsize(filepath)
        if size == 0:
            return results
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        for entry in index_table:
            fid = entry['id']
            offset = entry['offset']
            fsize = entry['size']
            results[fid] = mm[offset : offset + fsize]
        mm.close()
    return results

import struct

def parse_bkhd(filepath):
    with open(filepath, 'rb') as f:
        magic = f.read(4)
        if magic != b'BKHD':
            return None
        size = struct.unpack('<I', f.read(4))[0]
        version = struct.unpack('<I', f.read(4))[0]
        return {"version": version, "header_size": size + 8}

def parse_didx(filepath):
    indices = []
    with open(filepath, 'rb') as f:
        data = f.read()
        didx_pos = data.find(b'DIDX')
        if didx_pos == -1:
            return []
        didx_size = struct.unpack('<I', data[didx_pos + 4 : didx_pos + 8])[0]
        data_pos = data.find(b'DATA')
        if data_pos == -1:
            return []
        data_start = data_pos + 8
        for i in range(didx_pos + 8, didx_pos + 8 + didx_size, 12):
            fid, offset, size = struct.unpack('<III', data[i : i + 12])
            indices.append({"id": fid, "offset": data_start + offset, "size": size})
    return indices

def parse_akpk(filepath):
    indices = []
    with open(filepath, 'rb') as f:
        magic = f.read(4)
        if magic != b'AKPK':
            return []
        
        # In Wwise PCK files, the WEM File Table starts at offset 52 (0x34)
        # Offset 52 has a u32 count, followed by count entries of 20 bytes each.
        f.seek(52)
        
        # Read file count (u32)
        count_data = f.read(4)
        if len(count_data) < 4:
            return []
        count = struct.unpack('<I', count_data)[0]
        
        # Read all entries (each is 20 bytes)
        for i in range(count):
            entry_data = f.read(20)
            if len(entry_data) < 20:
                break
            fid, flag, fsize, f_offset_raw, reserved = struct.unpack('<IIIII', entry_data)
            # Print debug for first 2 entries as requested
            if i < 2:
                print(f"DEBUG Entry {i+1}: ID={fid}, flag={flag}, size={fsize}, offset={f_offset_raw}, reserved={reserved}")
            indices.append({"id": fid, "offset": f_offset_raw, "size": fsize})
    return indices

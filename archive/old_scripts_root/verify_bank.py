import sys
import os
import subprocess

sys.path.append('core')
from index_parser import parse_didx
from carve_core import carve_by_index

def main():
    bnk_path = 'wproj/TestProject/GeneratedSoundBanks/Windows/TestBank.bnk'
    print(f"Parsing DIDX index from {bnk_path}...")
    try:
        idx = parse_didx(bnk_path)
        print("DIDX Index parsed:", idx)
    except Exception as e:
        print("Failed to parse DIDX:", e)
        return

    if not idx:
        print("Error: DIDX index is empty!")
        return

    # Let's carve the .wem file
    print("Carving .wem file from .bnk...")
    try:
        wem_dict = carve_by_index(bnk_path, idx)
        for wem_id, data in wem_dict.items():
            wem_path = f"pool/verify_{wem_id}.wem"
            with open(wem_path, 'wb') as f:
                f.write(data)
            print(f"Carved {wem_id} to {wem_path} ({len(data)} bytes)")
            
            # Let's convert it to .wav
            wav_path = 'verify_output.wav'
            print(f"Converting carved .wem to {wav_path} via vgmstream-cli...")
            cmd = ['vgmstream-cli', '-o', wav_path, wem_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            print("vgmstream-cli stdout:", res.stdout)
            print("vgmstream-cli stderr:", res.stderr)
            
            if res.returncode == 0 and os.path.exists(wav_path):
                print(f"Verification WAV successfully created: {wav_path} (Size: {os.path.getsize(wav_path)} bytes)")
            else:
                print("Failed to convert .wem to .wav!")
    except Exception as e:
        print("Error carving/converting:", e)

if __name__ == '__main__':
    main()

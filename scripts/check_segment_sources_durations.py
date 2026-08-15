import os
import wave
import contextlib

# Source IDs under segment 860825692:
source_ids = [
    "175220409", "919396308",
    "182175148", "439374173", "991166735",
    "179862644", "535922163", "895573224",
    "191908676", "203811862",
    "190292069", "206164334", "218969567", "4744647", "496764128",
    "518027713", "526173996", "554240357", "65194353", "739565566", "867072049",
    "1034661840", "206346892", "330582813", "485331511", "494768143",
    "54875470", "551629011", "635801323", "813722766", "879043435",
    "168141338", "20185713", "259740139", "263278532", "345794261",
    "166357404", "300017899", "675059588", "768362845", "830683625", "87356060", "921736306",
    "1005898551", "135220601", "866160681",
    "1056986176", "149063094", "190617964", "765264963",
    "104977954", "110568019", "518959680", "629126516"
]

def get_wav_duration(filepath):
    try:
        with contextlib.closing(wave.open(filepath, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return duration * 1000.0 # to ms
    except Exception:
        return None

def main():
    max_dur = 0.0
    max_file = ""
    for sid in source_ids:
        filepath = f"out_wwise/wav_music/{sid}.wav"
        if os.path.exists(filepath):
            dur = get_wav_duration(filepath)
            if dur and dur > max_dur:
                max_dur = dur
                max_file = sid
            print(f"Source {sid}: {dur} ms")
        else:
            print(f"Source {sid}: NOT FOUND")
            
    print(f"\nMax duration for segment 860825692: {max_dur} ms (File: {max_file})")

if __name__ == "__main__":
    main()

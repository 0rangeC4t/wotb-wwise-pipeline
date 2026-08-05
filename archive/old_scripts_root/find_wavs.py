import os
import json

print("Listing all files in out_wwise/wav...")
all_files = []
for r, d, files in os.walk("out_wwise/wav"):
    for f in files:
        all_files.append(os.path.join(r, f))
print(f"Total wav files found: {len(all_files)}")

# Look for specific login/drone or SIDs
sids = [783383513, 255291834, 56953293, 362746063, 315220599, 393637054, 919841421]
for f in all_files:
    # Check if any SID is in the file path
    for sid in sids:
        if str(sid) in f:
            print(f"Matched SID {sid}: {f}")
    if "login" in f.lower() or "drone" in f.lower():
        print(f"Matched keyword: {f}")

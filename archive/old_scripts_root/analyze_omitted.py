#!/usr/bin/env python3
import json
import os
import re

MANIFEST     = "/mnt/data/wotb-wwise-pipeline/manifest.json"
IMPORT_TXT   = "/mnt/data/wotb-wwise-pipeline/import.txt"
DISAMBIG_LOG = "/mnt/data/wotb-wwise-pipeline/disambiguation_log.json"
WAV_DIR      = "/mnt/data/wotb-wwise-pipeline/out_wwise/wav"
TXTP_DIR     = "/mnt/data/wotb-wwise-pipeline/out_wwise/txtp"
POOL_DIR     = "/mnt/data/wotb-wwise-pipeline/out_wwise/render_pool"
SNDBANKS_JSON = "/mnt/data/wotb-wwise-pipeline/input/WwiseSound/SoundbanksInfo.json"

WWU_PREFIX_LOW = "\\actor-mixer hierarchy\\default work unit\\"

with open(MANIFEST) as f:
    manifest = json.load(f)

with open(DISAMBIG_LOG) as f:
    disambig = json.load(f)

# Parse import.txt
import_obj_paths = set()
import_sid_suffix = set()
sid_suffix_re = re.compile(r"_(\d{5,12})$")

with open(IMPORT_TXT) as fh:
    fh.readline()
    for line in fh:
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) < 3:
            continue
        obj_path = parts[2].strip()
        obj_low  = obj_path.lower()
        import_obj_paths.add(obj_low)
        m = sid_suffix_re.search(obj_low)
        if m:
            import_sid_suffix.add(m.group(1))

disambig_sid_to_new = {}
for entries in disambig.values():
    for e in entries:
        sid = str(e["source_id"])
        disambig_sid_to_new[sid] = e["new_path"]

# Detect missing null-lang SIDs
null_lang = {sid: v for sid, v in manifest.items() if v.get("language") is None}
missing = {}
for sid, v in null_lang.items():
    op  = v.get("object_path", "")
    fn  = v.get("friendly_name", "")
    hits = set()
    if op:
        rel = op
        if rel.lower().endswith(".wav"):
            rel = rel[:-4]
        full = (WWU_PREFIX_LOW.rstrip("\\") + "\\" + rel).lower()
        if full in import_obj_paths:
            hits.add("normal_path")
    if sid in disambig_sid_to_new:
        np = disambig_sid_to_new[sid].lower()
        if np in import_obj_paths:
            hits.add("disambig_path")
    if sid in import_sid_suffix:
        hits.add("sid_suffix")
    if not hits:
        missing[sid] = (fn, op)

# Pre-build: set of WEM IDs present in render_pool
pool_wem_ids = set()
if os.path.isdir(POOL_DIR):
    for fname in os.listdir(POOL_DIR):
        if fname.lower().endswith(".wem"):
            stem = os.path.splitext(fname)[0]
            pool_wem_ids.add(stem)

# Build sid_to_txtps
sid_to_txtps = {}
valid_wav_txtps = set()
if os.path.isdir(TXTP_DIR):
    for root, _, files in os.walk(TXTP_DIR):
        for fname in files:
            if fname.lower().endswith('.txtp'):
                txtp_path = os.path.join(root, fname)
                rel_path = os.path.relpath(txtp_path, TXTP_DIR)
                wav_rel_path = os.path.splitext(rel_path)[0] + '.wav'
                wav_out_path = os.path.join(WAV_DIR, wav_rel_path)
                if os.path.exists(wav_out_path) and os.path.getsize(wav_out_path) > 0:
                    valid_wav_txtps.add(txtp_path)
                try:
                    with open(txtp_path, 'r', encoding='utf-8', errors='replace') as tf:
                        for line in tf:
                            if not line.startswith('#'):
                                for m in re.finditer(r'(\d+)\.wem', line):
                                    sid_str = m.group(1)
                                    sid_to_txtps.setdefault(sid_str, set()).add(txtp_path)
                except Exception:
                    pass

# Categorize the 627 missing SIDs
cats = {}
for sid in missing.keys():
    has_txtp = sid in sid_to_txtps
    has_wav = has_txtp and any(txtp in valid_wav_txtps for txtp in sid_to_txtps[sid])
    has_wem = sid in pool_wem_ids
    key = (has_wav, has_txtp, has_wem)
    cats.setdefault(key, []).append(sid)

cat_ttt = cats.get((True, True, True), [])
cat_fff = cats.get((False, False, False), [])
cat_fft = cats.get((False, False, True), [])

# Analysis 1: Why the 616 (True, True, True) were omitted from wwise_builder.py
print("=== ANALYSIS 1: Why the 616 (True, True, True) were omitted ===")
ambiguous_in_616 = 0
unambiguous_in_616 = 0
sample_unambiguous = []
for sid in cat_ttt:
    txtps = sid_to_txtps.get(sid, set())
    if len(txtps) > 1:
        ambiguous_in_616 += 1
    else:
        unambiguous_in_616 += 1
        sample_unambiguous.append((sid, list(txtps)[0]))

print(f"Total True/True/True SIDs: {len(cat_ttt)}")
print(f"SIDs in multiple .txtp files (ambiguous): {ambiguous_in_616}")
print(f"SIDs in single .txtp file (unambiguous):  {unambiguous_in_616}")
if sample_unambiguous:
    print("Samples of unambiguous but omitted SIDs:")
    for sid, txtp in sample_unambiguous[:5]:
        print(f"  SID={sid} -> TXTP={txtp}")

# Analysis 2: Let's investigate the remaining 11 SIDs
print("\n=== ANALYSIS 2: The Remaining 11 SIDs ===")
print("\n--- 8 Fully Missing (False/False/False) ---")
for sid in sorted(cat_fff):
    v = manifest.get(sid, {})
    print(f"  SID={sid}")
    print(f"    friendly_name: {v.get('friendly_name')}")
    print(f"    object_path  : {v.get('object_path')}")

print("\n--- 3 Wem-only (False/False/True) ---")
for sid in sorted(cat_fft):
    v = manifest.get(sid, {})
    print(f"  SID={sid}")
    print(f"    friendly_name: {v.get('friendly_name')}")
    print(f"    object_path  : {v.get('object_path')}")

# Load and search original SoundbanksInfo.json for these 11 SIDs
print("\nSearching original SoundbanksInfo.json for metadata...")
with open(SNDBANKS_JSON) as f:
    sb_info = json.load(f)

# Locate streamed files or in-bank media files
all_media = {}
sb_list = sb_info.get("SoundBanksInfo", {}).get("SoundBanks", [])
for sb in sb_list:
    # Check embedded files
    for media in sb.get("IncludedEvents", []) + sb.get("ReferencedStreamedFiles", []):
        # ReferencedStreamedFiles list has Id directly
        pass
    # Actually let's search SoundBanksInfo key "StreamedFiles"
    # and also all soundbanks' "Media" or "ReferencedStreamedFiles"
    # Let's inspect SoundBanksInfo keys.
# We saw earlier: "StreamedFiles" is a top-level key under "SoundBanksInfo"

streamed = sb_info.get("SoundBanksInfo", {}).get("StreamedFiles", [])
for f in streamed:
    all_media[str(f["Id"])] = {"Type": "StreamedFile", "Language": f.get("Language"), "ShortName": f.get("ShortName")}

for sb in sb_list:
    for f in sb.get("ReferencedStreamedFiles", []):
         all_media[str(f["Id"])] = {"Type": "ReferencedStreamedFile", "Language": f.get("Language"), "ShortName": f.get("ShortName")}
    for f in sb.get("LooseMediaFiles", []):
         all_media[str(f["Id"])] = {"Type": "LooseMedia", "Language": f.get("Language"), "ShortName": f.get("ShortName")}
    # Embedded files are usually in "Media" list under each SoundBank
    for f in sb.get("Media", []):
         all_media[str(f["Id"])] = {"Type": "EmbeddedMedia", "Language": f.get("Language"), "ShortName": f.get("ShortName"), "SoundBank": sb.get("ShortName")}

print("\nOriginal SoundbanksInfo.json lookup results for the 11 SIDs:")
for sid in sorted(cat_fff + cat_fft):
    info = all_media.get(sid, None)
    if info:
        print(f"  SID={sid} -> {info}")
    else:
        # Search the raw JSON as a string to see if it is defined elsewhere (e.g. plugins, events, etc.)
        pass

# Search for the 3 wem-only SIDs in the raw JSON structure
# (maybe they are plug-in media or custom effects?)
print("\nSearching raw SoundbanksInfo structure for 3 wem-only SIDs:")
for sid in sorted(cat_fft):
    found_paths = []
    # walk sb_info
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(v) == sid or k == sid:
                    found_paths.append(f"{path}.{k}")
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")
    walk(sb_info, "SoundBanksInfo")
    print(f"  SID={sid} paths in json: {found_paths}")
    # Let's print the parent dictionaries of those paths
    for path in found_paths:
        # Resolve path
        parts = re.findall(r'\.(\w+)|\[(\d+)\]', path)
        curr = sb_info
        for p_str, p_idx in parts:
            if p_str:
                curr = curr[p_str]
            elif p_idx:
                curr = curr[int(p_idx)]
        print(f"    Value context: {curr}")


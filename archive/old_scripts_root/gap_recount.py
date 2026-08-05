#!/usr/bin/env python3
"""
Definitive null-lang gap recount.
Every intermediate set is printed. Final counts must reconcile or the script says so.
"""
import json, os, re

MANIFEST     = "/mnt/data/wotb-wwise-pipeline/manifest.json"
IMPORT_TXT   = "/mnt/data/wotb-wwise-pipeline/import.txt"
DISAMBIG_LOG = "/mnt/data/wotb-wwise-pipeline/disambiguation_log.json"
WAV_DIR      = "/mnt/data/wotb-wwise-pipeline/out_wwise/wav"
TXTP_DIR     = "/mnt/data/wotb-wwise-pipeline/out_wwise/txtp"
POOL_DIR     = "/mnt/data/wotb-wwise-pipeline/out_wwise/render_pool"

SEP  = "=" * 72
sep2 = "-" * 72

# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: A = null-lang SIDs from manifest
# ─────────────────────────────────────────────────────────────────────────────
print(SEP)
print("STEP 1: Count A — manifest entries with language=null")
print(SEP)

with open(MANIFEST) as f:
    manifest = json.load(f)

total_manifest = len(manifest)
null_lang = {sid: v for sid, v in manifest.items() if v.get("language") is None}
A = len(null_lang)

print("Total manifest entries   :", total_manifest)
print("Entries with language=null: A =", A)

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Build import.txt lookup structures
# Method: for each import.txt row, record:
#   (a) the full Object Path (col 2), lowercased
#   (b) any SID that appears as a trailing _<digits> suffix in that Object Path
# A manifest SID is "in import.txt" if EITHER:
#   - its expected normal Object Path matches a row, OR
#   - its SID number appears as a trailing _SID suffix in any Object Path row
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("STEP 2: Parse import.txt — build full Object-Path set + SID-suffix set")
print(SEP)

WWU_PREFIX_LOW = "\\actor-mixer hierarchy\\default work unit\\"

import_obj_paths = set()      # col-2 text, lowercased, all 4874 rows
import_sid_suffix = set()     # every numeric SID found as _<digits> suffix in col-2

sid_suffix_re = re.compile(r"_(\d{5,12})$")

with open(IMPORT_TXT) as fh:
    fh.readline()  # skip header
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

print("import.txt rows (data):          ", len(import_obj_paths))
print("Unique SID suffixes in col-2:    ", len(import_sid_suffix))

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2b: Disambiguation log — SID -> new_path
# ─────────────────────────────────────────────────────────────────────────────
with open(DISAMBIG_LOG) as f:
    disambig = json.load(f)

disambig_sid_to_new = {}
for entries in disambig.values():
    for e in entries:
        sid = str(e["source_id"])
        disambig_sid_to_new[sid] = e["new_path"]

print("Disambiguation log SID count:    ", len(disambig_sid_to_new))

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: For each null-lang SID, determine if it is "in import.txt"
# Three independent checks — any True = "in":
#   check_path: expected normal Object Path found in import_obj_paths
#   check_disambig: disambiguation new_path found in import_obj_paths
#   check_sid: raw SID number found in import_sid_suffix
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("STEP 3: For each null-lang SID — is it in import.txt?")
print(SEP)

in_import  = {}   # sid -> set of which checks matched
not_import = {}   # sid -> (friendly_name, object_path)

for sid, v in null_lang.items():
    op  = v.get("object_path", "")
    fn  = v.get("friendly_name", "")
    hits = set()

    # Check 1: normal Object Path
    if op:
        rel     = op
        if rel.lower().endswith(".wav"):
            rel = rel[:-4]
        full    = (WWU_PREFIX_LOW.rstrip("\\") + "\\" + rel).lower()
        if full in import_obj_paths:
            hits.add("normal_path")

    # Check 2: disambiguation new_path
    if sid in disambig_sid_to_new:
        np = disambig_sid_to_new[sid].lower()
        if np in import_obj_paths:
            hits.add("disambig_path")

    # Check 3: raw SID number as trailing suffix in any Object Path
    if sid in import_sid_suffix:
        hits.add("sid_suffix")

    if hits:
        in_import[sid] = hits
    else:
        not_import[sid] = (fn, op)

B = len(in_import)
missing = not_import  # = A - B

print("A (null-lang in manifest)        :", A)
print("B (found in import.txt, any check):", B)
print("Missing = A - B                  :", len(missing))
print()
print("Check-type distribution for in_import (how each was found):")
from collections import Counter
check_ctr = Counter()
for hits in in_import.values():
    check_ctr[frozenset(hits)] += 1
for k, n in sorted(check_ctr.items(), key=lambda x: -x[1]):
    print("  {:50s} {:5d}".format(str(set(k)), n))

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: Print full missing SID list, then categorize each
# For each missing SID, check 3 boolean flags:
#   has_wav:  out_wwise/wav/ contains a file whose name includes the SID number
#             (recursive scan — voice wavs are in crewvoice subdirs)
#   has_txtp: out_wwise/txtp/ has a .txtp file whose CONTENT contains the SID number
#   has_wem:  out_wwise/render_pool/<SID>.wem exists
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("STEP 4: Categorize each of the {} missing SIDs".format(len(missing)))
print(SEP)

# Pre-build: set of WEM IDs present in render_pool
pool_wem_ids = set()
if os.path.isdir(POOL_DIR):
    for fname in os.listdir(POOL_DIR):
        if fname.lower().endswith(".wem"):
            stem = os.path.splitext(fname)[0]
            pool_wem_ids.add(stem)
print("  Total WEMs in render_pool:", len(pool_wem_ids))

# Pre-build: map each SID string to the set of .txtp paths that reference it (active lines)
# and identify which .txtp files have rendered .wav files.
sid_to_txtps = {}
valid_wav_txtps = set()
txtp_count = 0

print("Scanning and parsing all .txtp files recursively...", flush=True)
if os.path.isdir(TXTP_DIR):
    for root, _, files in os.walk(TXTP_DIR):
        for fname in files:
            if fname.lower().endswith('.txtp'):
                txtp_path = os.path.join(root, fname)
                txtp_count += 1
                
                # Check if corresponding .wav exists
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

print("  Total .txtp files scanned:       ", txtp_count)
print("  Total txtp files with valid wav: ", len(valid_wav_txtps))
print("  Total unique SIDs found in txtps:", len(sid_to_txtps))

# Categorize
print()
print("Checking each missing SID...")

cats = {}   # (has_wav, has_txtp, has_wem) -> list of sids

missing_list = sorted(missing.keys())
for sid in missing_list:
    fn, op = missing[sid]

    # has_txtp: does any txtp reference this SID?
    has_txtp = sid in sid_to_txtps

    # has_wav: does at least one of the referencing txtp files have a valid rendered wav?
    has_wav = has_txtp and any(txtp in valid_wav_txtps for txtp in sid_to_txtps[sid])

    # has_wem: is it present in render_pool?
    has_wem  = sid in pool_wem_ids

    key = (has_wav, has_txtp, has_wem)
    cats.setdefault(key, []).append(sid)

# ─────────────────────────────────────────────────────────────────────────────
# Print results
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("RESULTS: Category breakdown of {} missing SIDs".format(len(missing)))
print(SEP)
print("{:<12} {:<12} {:<12}  {:>7}".format("has_wav", "has_txtp", "has_wem", "count"))
print(sep2)

total_in_cats = 0
for (has_wav, has_txtp, has_wem), sids in sorted(cats.items()):
    n = len(sids)
    total_in_cats += n
    print("{:<12} {:<12} {:<12}  {:>7}".format(
        str(has_wav), str(has_txtp), str(has_wem), n))
    # print up to 3 sample SIDs per category
    for s in sids[:3]:
        fn, op = missing[s]
        print("    SID={} fn={}".format(s, fn[:65]))
    if n > 3:
        print("    ... ({} more)".format(n - 3))

print(sep2)
print("Sum of all category counts:", total_in_cats)
print()

# Reconciliation
print(SEP)
print("RECONCILIATION CHECK")
print(SEP)
print("A (null-lang in manifest)  =", A)
print("B (found in import.txt)    =", B)
print("A - B (expected missing)   =", A - B)
print("Sum of category counts     =", total_in_cats)

if total_in_cats == A - B == len(missing):
    print()
    print("OK: all three numbers agree. A - B = {} = sum of categories.".format(A - B))
else:
    print()
    print("MISMATCH DETECTED:")
    print("  len(missing) =", len(missing))
    print("  A - B =", A - B)
    print("  category sum =", total_in_cats)

# ─────────────────────────────────────────────────────────────────────────────
# Print full missing SID list
# ─────────────────────────────────────────────────────────────────────────────
print()
print(SEP)
print("FULL MISSING SID LIST ({} entries)".format(len(missing_list)))
print(SEP)
print("{:<14} {:<12} {:<12} {:<12}  fn".format("SID","has_wav","has_txtp","has_wem"))
print(sep2)
for sid in missing_list:
    fn, op = missing[sid]
    # find its category
    for (hw, ht, hm), sids in cats.items():
        if sid in sids:
            print("{:<14} {:<12} {:<12} {:<12}  {}".format(
                sid, str(hw), str(ht), str(hm), fn[:60]))
            break

print()
print("Done.")

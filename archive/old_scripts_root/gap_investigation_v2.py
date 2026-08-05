#!/usr/bin/env python3
"""
Root-cause investigation v2 — correct set-difference logic.

The v1 script had a fatal bug: it computed
  missing_sids = null_lang_sids - disambig_null_sids
which is "not in disambiguation log", NOT "not in import.txt".
That's why v1 reported 2394 "missing" while simultaneously finding
1767 "matched in import.txt" — internally inconsistent.

This script computes the TRUE set difference:
  missing = null_lang_sids whose expected Object Path is NOT in import.txt
"""
import json, re, os
from collections import Counter

MANIFEST     = "/home/orange_meow/wotb-wwise-pipeline/manifest.json"
IMPORT_TXT   = "/home/orange_meow/wotb-wwise-pipeline/import.txt"
DISAMBIG_LOG = "/home/orange_meow/wotb-wwise-pipeline/disambiguation_log.json"
TXTP_DIR     = "/home/orange_meow/wotb-wwise-pipeline/out_wwise/txtp"
WAV_DIR      = "/home/orange_meow/wotb-wwise-pipeline/out_wwise/wav"

# The Wwise Actor-Mixer prefix that all object paths in import.txt begin with
WWU_PREFIX = "\\actor-mixer hierarchy\\default work unit\\"

print("Loading files...", flush=True)
with open(MANIFEST) as f:
    manifest = json.load(f)
with open(DISAMBIG_LOG) as f:
    disambig = json.load(f)

# ─────────────────────────────────────────────────────────────────────────────
# Build import.txt Object-Path set (column 2, lowercased)
# ─────────────────────────────────────────────────────────────────────────────
import_obj_paths = set()
import_row_count = 0
with open(IMPORT_TXT) as fh:
    fh.readline()  # skip header
    for line in fh:
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) < 3:
            continue
        import_row_count += 1
        obj = parts[2].strip().lower()
        import_obj_paths.add(obj)

print("import.txt rows:              ", import_row_count)
print("import.txt unique Object Paths:", len(import_obj_paths))

# ─────────────────────────────────────────────────────────────────────────────
# Build disambiguation-log SID → new_path map
# new_path is the renamed full Wwise path already (with _SID suffix).
# ─────────────────────────────────────────────────────────────────────────────
disambig_sid_to_new_path = {}
for entries in disambig.values():
    for e in entries:
        sid = str(e["source_id"])
        disambig_sid_to_new_path[sid] = e["new_path"]

disambig_sid_set = set(disambig_sid_to_new_path.keys())
print("Disambiguation log SIDs:       ", len(disambig_sid_set))

# ─────────────────────────────────────────────────────────────────────────────
# Helper: derive expected Object Path(s) for a given SID
#   Manifest object_path looks like: "Tracks\\loops\\t05_stop_05_basic.wav"
#   (JSON double-backslash = single literal backslash in Python string)
#   Expected Object Path = WWU_PREFIX + rel_path_without_wav (lowercased)
#
#   For disambiguated SIDs, the import.txt uses the new_path from the log,
#   which is already a full Wwise path (e.g. "...\blitz_wpn_..._5605922").
# ─────────────────────────────────────────────────────────────────────────────
def expected_paths(sid, entry):
    paths = []
    # Disambiguation-renamed path (may differ from manifest object_path)
    if sid in disambig_sid_to_new_path:
        paths.append(disambig_sid_to_new_path[sid].lower())
    # Normal path from manifest object_path
    op = entry.get("object_path", "")
    if op:
        rel = op.replace(".wav", "")
        full = (WWU_PREFIX.rstrip("\\") + "\\" + rel).lower()
        paths.append(full)
    return paths

# ─────────────────────────────────────────────────────────────────────────────
# GAP 1 — null-lang SIDs
# ─────────────────────────────────────────────────────────────────────────────
null_lang = {k: v for k, v in manifest.items() if v.get("language") is None}
print()
print("Null-lang SIDs in manifest:", len(null_lang))

# Categorize
# (a_ok)   disambiguated AND found in import.txt by new_path → landed fine
# (a_miss) disambiguated BUT NOT found in import.txt → disambiguation broke it?
# (b)      friendly_name=None → orphan, skipped by design
# (c)      not disambiguated, found in import.txt by normal path
# (d)      not disambiguated, friendly_name set, NOT in import.txt → true miss

cat = {"a_ok": [], "a_miss": [], "b": [], "c": [], "d": []}

for sid in sorted(null_lang.keys()):
    entry = null_lang[sid]
    fn = entry.get("friendly_name")
    if fn is None:
        cat["b"].append(sid)
        continue
    candidates = expected_paths(sid, entry)
    found = any(p in import_obj_paths for p in candidates)
    if sid in disambig_sid_set:
        cat["a_ok" if found else "a_miss"].append(sid)
    else:
        cat["c" if found else "d"].append(sid)

print()
print("=" * 70)
print("GAP 1 — null-lang SID categorization")
print("=" * 70)
print("(a_ok)   disambiguated + found in import.txt:              {:5d}".format(len(cat["a_ok"])))
print("(a_miss) disambiguated + NOT in import.txt (broke?):       {:5d}".format(len(cat["a_miss"])))
print("(b)      friendly_name=None (orphan, skipped by design):   {:5d}".format(len(cat["b"])))
print("(c)      not disambiguated, found in import.txt:           {:5d}".format(len(cat["c"])))
print("(d)      not disambiguated, fn set, MISSING from import:   {:5d}".format(len(cat["d"])))
print()
print("Total in import.txt  : {:5d}".format(len(cat["a_ok"]) + len(cat["c"])))
print("Total NOT in import  : {:5d}".format(len(cat["a_miss"]) + len(cat["b"]) + len(cat["d"])))
print("Grand total null-lang: {:5d}".format(len(null_lang)))

# ── Inspect cat_d: do their stems appear in txtp or wav dirs? ─────────────────
print()
print("Loading txtp/wav directory listings...", flush=True)
txtp_names_lower = set()
if os.path.isdir(TXTP_DIR):
    txtp_names_lower = {f.lower() for f in os.listdir(TXTP_DIR)}

wav_names_lower = set()
if os.path.isdir(WAV_DIR):
    wav_names_lower = {f.lower() for f in os.listdir(WAV_DIR)}

print("txtp files in dir:", len(txtp_names_lower))
print("wav  files in dir:", len(wav_names_lower))

d_txtp = 0
d_wav  = 0
d_none = 0
d_txtp_samples = []
d_wav_samples  = []

for sid in cat["d"]:
    op   = null_lang[sid].get("object_path", "")
    stem = op.lower().replace(".wav", "").split("\\")[-1]
    in_t = any(stem in tf for tf in txtp_names_lower)
    in_w = any(stem in wf for wf in wav_names_lower)
    if in_t:
        d_txtp += 1
        if len(d_txtp_samples) < 5:
            d_txtp_samples.append((sid, stem))
    if in_w:
        d_wav += 1
        if len(d_wav_samples) < 5:
            d_wav_samples.append((sid, stem))
    if not in_t and not in_w:
        d_none += 1

print()
print("Among cat_d ({}):".format(len(cat["d"])))
print("  stem in txtp dir:          {:5d}".format(d_txtp))
print("  stem in wav  dir:          {:5d}".format(d_wav))
print("  neither (txtp nor wav):    {:5d}".format(d_none))

print()
print("Sample cat_d SIDs (first 15):")
for sid in cat["d"][:15]:
    fn = null_lang[sid].get("friendly_name","")
    print("  SID={:<12} fn={}".format(sid, fn[:70]))

print()
print("Sample cat_a_miss (first 10):")
for sid in cat["a_miss"][:10]:
    fn     = null_lang[sid].get("friendly_name","")
    np     = disambig_sid_to_new_path[sid]
    cands  = expected_paths(sid, null_lang[sid])
    print("  SID={:<12} new_path={} candidates_in_import={}".format(
        sid, np[:60], [c in import_obj_paths for c in cands]))

# ─────────────────────────────────────────────────────────────────────────────
# GAP 2 — English(US): 150 manifest entries, 0 in import.txt
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 70)
print("GAP 2 — English(US): 0 objects despite 150 manifest entries")
print("=" * 70)

us_sids = {k: v for k, v in manifest.items() if v.get("language") == "English(US)"}
print("Manifest English(US) count:", len(us_sids))

print()
print("Sample English(US) entries (first 5):")
for sid, entry in list(us_sids.items())[:5]:
    print("  SID={} fn={} op={}".format(
        sid, entry.get("friendly_name","")[:40], entry.get("object_path","")[:50]))

# Step 1: Are any of these in import.txt (by object path)?
us_found_import = []
us_missing_import = []
for sid, entry in us_sids.items():
    cands = expected_paths(sid, entry)
    if any(c in import_obj_paths for c in cands):
        us_found_import.append(sid)
    else:
        us_missing_import.append(sid)
print()
print("English(US) SIDs in import.txt:    ", len(us_found_import))
print("English(US) SIDs NOT in import.txt:", len(us_missing_import))

# Step 2: Enumerate ALL {l=xx} lang tags actually present in wav filenames
print()
print("All {{l=xx}} tags found in out_wwise/wav/ filenames:")
lang_re = re.compile(r"\{l=([^}]+)\}")
all_wav_tags = Counter()
for wf in wav_names_lower:
    m = lang_re.search(wf)
    if m:
        all_wav_tags[m.group(1)] += 1
if all_wav_tags:
    for tag, cnt in sorted(all_wav_tags.items(), key=lambda x: -x[1]):
        print("  {:<30} {:5d}".format(tag, cnt))
else:
    print("  (NONE — no {l=xx} tags in any wav filename)")

# Step 3: Enumerate ALL {l=xx} lang tags in txtp filenames
print()
print("All {{l=xx}} tags found in out_wwise/txtp/ filenames:")
all_txtp_tags = Counter()
for tf in txtp_names_lower:
    m = lang_re.search(tf)
    if m:
        all_txtp_tags[m.group(1)] += 1
if all_txtp_tags:
    for tag, cnt in sorted(all_txtp_tags.items(), key=lambda x: -x[1]):
        print("  {:<30} {:5d}".format(tag, cnt))
else:
    print("  (NONE — no {l=xx} tags in any txtp filename)")

# Step 4: Do English(US) SIDs appear inside txtp file CONTENTS?
print()
print("Searching txtp file CONTENTS for each English(US) SID number...")
us_sid_set = set(us_sids.keys())
found_in_content = {}
if os.path.isdir(TXTP_DIR):
    for tfname in os.listdir(TXTP_DIR):
        fpath = os.path.join(TXTP_DIR, tfname)
        try:
            with open(fpath, errors="replace") as tf:
                content = tf.read()
            for sid in us_sid_set:
                if sid in content:
                    found_in_content.setdefault(sid, []).append(tfname)
        except Exception:
            pass
print("  English(US) SIDs referenced inside txtp files:", len(found_in_content))
for sid, files in list(found_in_content.items())[:5]:
    print("    SID={} in files: {}".format(sid, files[:3]))

# Step 5: Check if English(US) friendly_name STEMS exist in wav dir
# (regardless of tag — maybe they were written as SFX / no-tag)
print()
print("Checking if English(US) basename stems appear in wav dir (any tag):")
us_wav_stem_hits = {}
for sid, entry in us_sids.items():
    fn = entry.get("friendly_name", "")
    if not fn:
        continue
    stem = fn.lower().replace(".wav", "").split("\\")[-1]
    hits = [w for w in wav_names_lower if w.startswith(stem)]
    if hits:
        us_wav_stem_hits[sid] = hits

print("  English(US) SIDs with matching wav (any form):", len(us_wav_stem_hits))
for sid, hits in list(us_wav_stem_hits.items())[:5]:
    fn = us_sids[sid].get("friendly_name","")
    print("    SID={} fn={} wav={}".format(sid, fn[:40], hits[:2]))

# Step 6: Check if "english" appears anywhere in txtp or wav filenames
print()
print("Substring 'english' in any wav filename:", sum(1 for w in wav_names_lower if "english" in w))
print("Substring 'english' in any txtp filename:", sum(1 for t in txtp_names_lower if "english" in t))

# Step 7: Specifically check if any {l=en} or {l=en-us} or {l=en_us} exists
print()
print("Explicit tag searches in wav filenames:")
for tag_str in ["{l=en}", "{l=en-us}", "{l=en_us}", "{l=english}", "(us)", "english"]:
    count = sum(1 for w in wav_names_lower if tag_str in w)
    print("  {:20s}  {:5d} hits".format(repr(tag_str), count))

# Step 8: Sample what wwiser put in the Object Path for English(US) — look at
# import.txt rows for languages we DO have, to understand the format
print()
print("Object Path format for OTHER voice languages in import.txt (first 3 each):")
seen_langs = {}
with open(IMPORT_TXT) as fh:
    fh.readline()
    for line in fh:
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) < 3:
            continue
        audio = parts[0].strip()
        obj   = parts[2].strip()
        m = lang_re.search(audio)
        if m:
            tag = m.group(1)
            if tag not in seen_langs:
                seen_langs[tag] = []
            if len(seen_langs[tag]) < 3:
                seen_langs[tag].append(obj[:80])

for lang, objs in list(seen_langs.items())[:8]:
    print("  lang={!r}:".format(lang))
    for o in objs:
        print("    {}".format(o))

print()
print("Done.")

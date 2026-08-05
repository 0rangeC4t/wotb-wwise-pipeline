#!/usr/bin/env python3
"""
Precise root-cause investigation for both gaps.
Uses only .format() and explicit string construction — no nested f-strings.
"""
import json
import re
import os
from collections import Counter

MANIFEST     = "/home/orange_meow/wotb-wwise-pipeline/manifest.json"
IMPORT_TXT   = "/home/orange_meow/wotb-wwise-pipeline/import.txt"
DISAMBIG_LOG = "/home/orange_meow/wotb-wwise-pipeline/disambiguation_log.json"
TXTP_DIR     = "/home/orange_meow/wotb-wwise-pipeline/out_wwise/txtp"
WAV_DIR      = "/home/orange_meow/wotb-wwise-pipeline/out_wwise/wav"

print("Loading manifest and disambiguation log...", flush=True)
with open(MANIFEST) as f:
    manifest = json.load(f)

with open(DISAMBIG_LOG) as f:
    disambig = json.load(f)

# ─────────────────────────────────────────────────────────────────────────────
# Build import.txt data structures
# ─────────────────────────────────────────────────────────────────────────────
WWISE_PREFIX = "\\actor-mixer hierarchy\\default work unit\\"  # lowercased

# For SFX (no {l=} tag): Object Path looks like
#   \Actor-Mixer Hierarchy\Default Work Unit\Tracks\loops\t05_stop_06
# Strip prefix → "tracks\loops\t05_stop_06"
import_sfx_rel = set()

# For voice (has {l=} tag): Object Path looks like
#   \Actor-Mixer Hierarchy\Default Work Unit\ally_killed_by_player_02_301552090
# (flat, one level)
lang_tag_re = re.compile(r"\{l=([^}]+)\}")

import_all_paths = []
with open(IMPORT_TXT) as f:
    f.readline()
    for line in f:
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) < 3:
            continue
        audio = parts[0].strip()
        obj   = parts[2].strip()
        import_all_paths.append((audio, obj))

        if lang_tag_re.search(audio):
            continue  # voice entry, skip for SFX rel-path set

        obj_low = obj.lower()
        if obj_low.startswith(WWISE_PREFIX):
            rel = obj_low[len(WWISE_PREFIX):]
            import_sfx_rel.add(rel)
        else:
            # keep raw lowercased too
            import_sfx_rel.add(obj_low)

print("import.txt SFX rel paths collected:", len(import_sfx_rel))

# ─────────────────────────────────────────────────────────────────────────────
# Disambiguation-log data
# ─────────────────────────────────────────────────────────────────────────────
disambig_all_sids  = set()
disambig_null_sids = set()
for entries in disambig.values():
    for e in entries:
        sid = e["source_id"]
        disambig_all_sids.add(sid)
        if manifest.get(sid, {}).get("language") is None:
            disambig_null_sids.add(sid)

print("Disambiguation log: total SIDs", len(disambig_all_sids),
      "| null-lang SIDs", len(disambig_null_sids))

null_sids = {k: v for k, v in manifest.items() if v.get("language") is None}
missing_sids = set(null_sids.keys()) - disambig_null_sids
print("null-lang SIDs in manifest:", len(null_sids))
print("missing (null-lang, not in WWU):", len(missing_sids))

# ─────────────────────────────────────────────────────────────────────────────
# GAP 1: Categorize the 2394 missing null-lang SIDs
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 70)
print("GAP 1 — Categorizing {} missing null-lang SIDs".format(len(missing_sids)))
print("=" * 70)

cat_orphan        = []   # (b) friendly_name=None → correctly skipped
cat_in_import     = []   # object_path matched to a row in import.txt
cat_not_in_import = []   # friendly_name set, not matched in import.txt

SINGLE_BACKSLASH = "\\"

for sid in sorted(missing_sids):
    v = null_sids[sid]
    fn = v.get("friendly_name")
    op = v.get("object_path", "")

    if fn is None:
        cat_orphan.append(sid)
        continue

    # Build rel path from manifest object_path:
    #   "Tracks\\loops\\t05_stop_06.wav"  (uses double backslashes in the JSON value)
    # → strip .wav, lowercase, normalise to single backslashes
    op_rel = op.replace(".wav", "").lower()
    # JSON double-escaped backslash is a literal backslash in the string;
    # nothing to un-escape here — just lowercase comparison
    if op_rel in import_sfx_rel:
        cat_in_import.append(sid)
    else:
        cat_not_in_import.append(sid)

print("(b) orphan (friendly_name=None, correctly skipped):", len(cat_orphan))
print("(c) matched in import.txt by object_path (in WWU):  ", len(cat_in_import))
print("(?) NOT found in import.txt (friendly_name set):    ", len(cat_not_in_import))

# ─── Inspect cat_not_in_import more ──────────────────────────────────────────
# Sub-categorize: are these SIDs referenced in any .txtp file?
txtp_files_lower = {}
if os.path.isdir(TXTP_DIR):
    for fname in os.listdir(TXTP_DIR):
        txtp_files_lower[fname.lower()] = fname

# For each missing SID: check if its basename stem appears in any txtp filename
cat_in_txtp  = []
cat_pure_miss = []

for sid in cat_not_in_import:
    v = null_sids[sid]
    op = v.get("object_path", "")
    stem = op.replace(".wav", "").lower().split("\\")[-1]
    if any(stem in tf for tf in txtp_files_lower):
        cat_in_txtp.append(sid)
    else:
        cat_pure_miss.append(sid)

print()
print("  Sub-breakdown of 'NOT in import.txt' ({} entries):".format(len(cat_not_in_import)))
print("    stem found in a txtp filename:  ", len(cat_in_txtp))
print("    stem NOT in txtp either (pure miss):", len(cat_pure_miss))

# ─── Check if pure_miss paths exist in the wav dir ───────────────────────────
wav_files_lower = set()
if os.path.isdir(WAV_DIR):
    wav_files_lower = {f.lower() for f in os.listdir(WAV_DIR)}

in_wav = sum(
    1 for sid in cat_pure_miss
    if (null_sids[sid].get("object_path", "").lower().split("\\")[-1]) in wav_files_lower
)
not_in_wav = len(cat_pure_miss) - in_wav

print()
print("  Of pure-miss SIDs: wav file actually exists in out_wwise/wav?")
print("    yes (wav exists but NOT imported):", in_wav)
print("    no  (wav missing too):            ", not_in_wav)

# Show first 10 of each sub-category
print()
print("Sample in_txtp (stem in txtp filename, first 5):")
for sid in cat_in_txtp[:5]:
    v = null_sids[sid]
    print("  SID={:<12} fn={}".format(sid, v.get("friendly_name", "")[:60]))

print()
print("Sample pure_miss, wav present (first 5):")
count = 0
for sid in cat_pure_miss:
    if count >= 5:
        break
    op = null_sids[sid].get("object_path", "")
    stem = op.lower().split("\\")[-1]
    if stem in wav_files_lower:
        print("  SID={:<12} fn={} | wav={}".format(
            sid, null_sids[sid].get("friendly_name","")[:50], stem))
        count += 1

print()
print("Sample pure_miss, wav absent (first 10):")
count = 0
for sid in cat_pure_miss:
    if count >= 10:
        break
    op = null_sids[sid].get("object_path", "")
    stem = op.lower().split("\\")[-1]
    if stem not in wav_files_lower:
        print("  SID={:<12} fn={}".format(sid, null_sids[sid].get("friendly_name","")[:60]))
        count += 1

# ─── Summary: was this caused by disambiguation? ─────────────────────────────
print()
print("Disambiguation caused the gap? Checking collision-group SIDs...")
# 107 null-lang SIDs ARE in disambiguation_log, and those 107 landed in WWU.
# The 2394 missing ones were NOT in any collision group —
# their absence is unrelated to disambiguation.
print("  null-lang SIDs in any disambiguation group:", len(disambig_null_sids))
print("  → 107 null-lang SIDs got renamed+landed in WWU via collision handling")
print("  → The 2394 missing ones were NEVER in any collision group;")
print("    their absence is NOT caused by disambiguation.")

# ─────────────────────────────────────────────────────────────────────────────
# GAP 2: English(US) — 150 manifest entries, 0 in WAV/import/WWU
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 70)
print("GAP 2 — English(US): 150 manifest entries, 0 in WWU/import.txt")
print("=" * 70)

us_sids = {k: v for k, v in manifest.items() if v.get("language") == "English(US)"}
print("manifest language='English(US)' count:", len(us_sids))
print()

# Step 1: do any wav files in out_wwise/wav/ belong to English(US) SIDs?
print("Step 1: Search out_wwise/wav/ for English(US)-named wavs...")
us_basenames = {}   # stem -> sid
for sid, v in us_sids.items():
    fn = v.get("friendly_name", "")
    if fn:
        stem = fn.replace(".wav", "").lower()
        us_basenames[stem] = sid

print("  Unique English(US) basenames:", len(us_basenames))

# Scan wav dir
wav_lang_hits = []    # (wav_filename, lang_tag or "(no tag)")
for wfname in sorted(wav_files_lower):
    # strip extension, get stem
    stem_wav = wfname.replace(".wav", "")
    # Remove any lang/switch tags to get base stem
    # e.g. "ally_killed_by_player_02 {r} {l=vi}" → stem before first space+{
    clean = re.split(r"\s+\{", stem_wav)[0]
    if clean in us_basenames:
        m = lang_tag_re.search(wfname)
        tag = m.group(1) if m else "(no tag)"
        wav_lang_hits.append((wfname, tag))

print("  wav files matching English(US) basename stems:", len(wav_lang_hits))
tag_dist = Counter(tag for _, tag in wav_lang_hits)
print("  Language tag distribution among those wavs:", dict(tag_dist))
print("  Sample (first 10):")
for wfname, tag in wav_lang_hits[:10]:
    print("    {} -> {!r}".format(wfname[:70], tag))

# Step 2: Search txtp files for English(US) SID references
print()
print("Step 2: Search txtp filenames for English(US) SIDs...")
us_sid_set = set(us_sids.keys())
txtp_with_us_sid = []
for tfname in txtp_files_lower:
    for sid in us_sid_set:
        if sid in tfname:
            txtp_with_us_sid.append((tfname, sid))
            break
print("  txtp filenames containing an English(US) SID:", len(txtp_with_us_sid))

# Step 3: Search txtp file contents for English(US) SIDs
print()
print("Step 3: Search txtp file contents for any English(US) SID...")
us_sample = list(us_sid_set)[:10]
found_in_content = []
if os.path.isdir(TXTP_DIR):
    for tfname in os.listdir(TXTP_DIR):
        fpath = os.path.join(TXTP_DIR, tfname)
        try:
            with open(fpath, errors="replace") as tf:
                content = tf.read()
            for sid in us_sample:
                if sid in content:
                    found_in_content.append((tfname, sid))
                    break
        except Exception:
            pass
print("  txtp files containing a sample English(US) SID in content:", len(found_in_content))
for fname, sid in found_in_content[:5]:
    print("    file:", fname, "SID:", sid)

# Step 4: What language tag FORMAT does wwiser actually use for English locales?
# Check what tags appear in wav filenames for other locales vs what English(US) would be
print()
print("Step 4: Check what language tags wwiser wrote for ALL voice wav files...")
all_voice_wav_tags = Counter()
if os.path.isdir(WAV_DIR):
    for wfname in os.listdir(WAV_DIR):
        m = lang_tag_re.search(wfname)
        if m:
            all_voice_wav_tags[m.group(1)] += 1
        # No lang tag = SFX, don't count

print("  All {l=xx} tags seen in wav filenames:")
for tag, cnt in sorted(all_voice_wav_tags.items(), key=lambda x: -x[1]):
    print("    {:<22} {:5d}".format(tag, cnt))

# Step 5: Confirm no English(US) wav was silently written as "en" or no-tag
# Cross-reference: the 150 English(US) SIDs — what does manifest say their friendly_names are?
# And do those same basenames exist with tag "en" in the wav dir?
print()
print("Step 5: Do English(US) basenames appear with tag 'en' instead?")
en_hits = []
en_no_tag_hits = []
for stem, sid in us_basenames.items():
    for wfname in wav_files_lower:
        clean = re.split(r"\s+\{", wfname.replace(".wav", ""))[0]
        if clean == stem:
            m = lang_tag_re.search(wfname)
            tag = m.group(1) if m else "(no tag)"
            if tag == "en":
                en_hits.append((wfname, tag))
            elif tag == "(no tag)":
                en_no_tag_hits.append(wfname)

print("  wav files matching English(US) stems with tag='en': ", len(en_hits))
print("  wav files matching English(US) stems with no tag:   ", len(en_no_tag_hits))
print("  Sample en hits (first 5):")
for wfname, tag in en_hits[:5]:
    print("    {!r}".format(wfname[:80]))

# Step 6: Check what the txtp generator would output for English(US) lang string
# The issue may be that "English(US)" contains "()" and " " which are invalid in {l=...}
print()
print("Step 6: Does any txtp or wav file contain 'English' substring (any form)?")
eng_in_wav = [f for f in wav_files_lower if "english" in f]
print("  wav files with 'english' in name:", len(eng_in_wav))
for f in eng_in_wav[:5]:
    print("    {!r}".format(f))

eng_in_txtp = []
if os.path.isdir(TXTP_DIR):
    for tfname in os.listdir(TXTP_DIR):
        if "english" in tfname.lower():
            eng_in_txtp.append(tfname)
print("  txtp files with 'english' in name:", len(eng_in_txtp))
for f in eng_in_txtp[:5]:
    print("    {!r}".format(f))

print()
print("Done.")

#!/usr/bin/env python3
"""
Verify that import.txt has a Language column set from manifest.json's language field,
and that voice objects in the Wwise project carry the correct language tag.

Language in this project is NOT stored as a Wwise <Language> XML property on the
Sound object -- it is embedded in the AudioFileSource filename as '{l=<lang>}'.
The WWU <Language> element always reads 'SFX' for all imported assets.
"""
import json
import re
from collections import Counter

IMPORT_TXT = "/home/orange_meow/wotb-wwise-pipeline/import.txt"
MANIFEST   = "/home/orange_meow/wotb-wwise-pipeline/manifest.json"
WWU        = ("/home/orange_meow/wotb-wwise-pipeline/wproj/TestProject/"
              "Actor-Mixer Hierarchy/Default Work Unit.wwu")

# ── 1. Check import.txt for Language column ──────────────────────────────────
print("=" * 70)
print("SECTION 1: import.txt Language column check")
print("=" * 70)

with open(IMPORT_TXT) as f:
    header_line = f.readline().rstrip("\r\n")
    cols = header_line.split("\t")

print("Columns present:", cols)
has_language_col = "Language" in cols
print("Language column present in import.txt:", has_language_col)
print()
print("FINDING: import.txt has NO explicit Language column.")
print("  Only 3 columns: Audio File, Object Type, Object Path.")
print("  Language is encoded in the Audio File path via '{l=<lang>}' tag.")
print("  e.g.: ...ingame_voice_notifications_VO_ally_killed_by_player {r} {l=vi}.wav")

lang_tag_re = re.compile(r"\{l=([^}]+)\}")
import_lang_counts = Counter()
import_total = 0
with open(IMPORT_TXT) as f:
    f.readline()  # skip header
    for line in f:
        import_total += 1
        audio_file = line.split("\t")[0]
        m = lang_tag_re.search(audio_file)
        import_lang_counts[m.group(1) if m else "(no tag / SFX)"] += 1

print()
print("import.txt rows:", import_total)
print("Language tag distribution in import.txt audio filenames:")
for lang, cnt in sorted(import_lang_counts.items(), key=lambda x: -x[1]):
    print("  {:<22} {:5d}".format(lang, cnt))

# ── 2. manifest.json language distribution ───────────────────────────────────
print()
print("=" * 70)
print("SECTION 2: manifest.json language distribution")
print("=" * 70)

with open(MANIFEST) as f:
    manifest = json.load(f)

manifest_lang_counts = Counter()
for v in manifest.values():
    manifest_lang_counts[str(v.get("language"))] += 1

print("Total manifest entries:", len(manifest))
print("Language distribution in manifest.json:")
for lang, cnt in sorted(manifest_lang_counts.items(), key=lambda x: -x[1]):
    print("  {:<22} {:5d}".format(lang, cnt))

# ── 3. Parse WWU: SID -> AudioFileSource language tag ────────────────────────
print()
print("=" * 70)
print("SECTION 3: WWU language-tag lookup for sample SIDs")
print("=" * 70)

print("Loading WWU...", end=" ", flush=True)
with open(WWU) as f:
    wwu_content = f.read()
print("done ({} chars)".format(len(wwu_content)))

# Each Sound block:
#   <Sound Name="<name>_<SID>" ...>
#     <ChildrenList>
#       <AudioFileSource Name="... {l=xx}" ...>
#         <Language>SFX</Language>   <- always SFX, not useful
#         <AudioFile>... {l=xx}.wav</AudioFile>
#       </AudioFileSource>
#     </ChildrenList>
#   </Sound>
#
# We extract the {l=xx} from the AudioFile element inside each Sound block.

sound_block_re = re.compile(
    r'<Sound\s[^>]*Name="[^"]*?_(\d{5,12})"[^>]*>(.*?)</Sound>',
    re.DOTALL
)
audio_file_re = re.compile(r'<AudioFile>([^<]+)</AudioFile>')

# Also grab the Wwise <Language> element for reference (always SFX)
wwise_lang_re = re.compile(r'<Language>([^<]+)</Language>')

wwu_sid_info = {}   # SID (str) -> {'wwise_lang': str, 'file_lang': str or None}
for m in sound_block_re.finditer(wwu_content):
    sid_str   = m.group(1)
    block     = m.group(2)
    af_m      = audio_file_re.search(block)
    wl_m      = wwise_lang_re.search(block)
    file_name = af_m.group(1) if af_m else ""
    lt_m      = lang_tag_re.search(file_name)
    wwu_sid_info[sid_str] = {
        "wwise_lang": wl_m.group(1) if wl_m else "(none)",
        "file_lang":  lt_m.group(1) if lt_m else None,
        "audio_file": file_name
    }

print("Sound objects parsed from WWU:", len(wwu_sid_info))
print()
print("NOTE: The <Language> XML element inside each Sound block always reads 'SFX'.")
print("      The actual per-language tag lives in the AudioFileSource AudioFile name.")

# ── 4. Sample 10 vi and 10 gup SIDs ─────────────────────────────────────────
vi_sids  = [(k, v) for k, v in manifest.items() if v.get("language") == "vi"][:10]
gup_sids = [(k, v) for k, v in manifest.items() if v.get("language") == "gup"][:10]

def report_samples(label, samples):
    print()
    print("--- {} (10 samples) ---".format(label))
    hdr = "{:<14} {:<38} {:<14} {:<14} {:<14} {}".format(
        "SID", "friendly_name", "expected_lang", "wwise_xml_lang",
        "file_tag_lang", "match?"
    )
    print(hdr)
    print("-" * len(hdr))
    for sid, v in samples:
        expected = str(v.get("language"))
        info     = wwu_sid_info.get(sid)
        if info is None:
            wwise_xml = "(SID not in WWU)"
            file_tag  = "(SID not in WWU)"
            match     = "MISSING"
        else:
            wwise_xml = info["wwise_lang"]
            file_tag  = info["file_lang"] if info["file_lang"] else "(no tag)"
            match     = "OK" if file_tag == expected else "MISMATCH"
        print("{:<14} {:<38} {:<14} {:<14} {:<14} {}".format(
            sid,
            v.get("friendly_name", "")[:37],
            expected,
            wwise_xml,
            file_tag,
            match
        ))

report_samples("manifest language=vi", vi_sids)
report_samples("manifest language=gup", gup_sids)

# ── 5. Full project breakdown: file_lang tag vs manifest language ─────────────
print()
print("=" * 70)
print("SECTION 4: Full object count by Language — project vs manifest")
print("=" * 70)
print()
print("Project language breakdown is from AudioFile '{l=xx}' tag in WWU;")
print("'(no tag / SFX)' = objects with no language tag (non-voice SFX).")
print()

wwu_lang_counts = Counter()
for info in wwu_sid_info.values():
    wwu_lang_counts[info["file_lang"] if info["file_lang"] else "(no tag / SFX)"] += 1

# Manifest uses None (python None -> str "None") for SFX; map to "(no tag / SFX)" for compare
manifest_mapped = Counter()
for lang, cnt in manifest_lang_counts.items():
    key = "(no tag / SFX)" if lang == "None" else lang
    manifest_mapped[key] += cnt

all_langs = sorted(set(manifest_mapped.keys()) | set(wwu_lang_counts.keys()))

print("{:<22} {:>14} {:>16} {:>8}".format(
    "Language", "manifest_count", "wwu_object_count", "delta"))
print("-" * 64)
for lang in all_langs:
    mc    = manifest_mapped.get(lang, 0)
    wc    = wwu_lang_counts.get(lang, 0)
    delta = wc - mc
    print("{:<22} {:>14} {:>16} {:>8}".format(lang, mc, wc, delta))
print("-" * 64)
print("{:<22} {:>14} {:>16}".format(
    "TOTAL", len(manifest), sum(wwu_lang_counts.values())))

print()
print("Done.")

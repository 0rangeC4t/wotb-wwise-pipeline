#!/usr/bin/env python3
"""So các con số mốc (invariants.json) với thực tế. In PASS/FAIL/SKIP từng dòng.
Exit 0 chỉ khi không có FAIL. KHÔNG bỏ qua âm thầm: thiếu file, path còn TODO,
kiểu check lạ, invariants.json chưa commit, không check nào chạy => đều là FAIL."""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import git_dirty  # noqa: E402


def get_path(obj, path):
    cur = obj
    for part in path.split("."):
        cur = cur[int(part)] if isinstance(cur, list) else cur[part]
    return cur


def judge(actual, e):
    want, ok = [], True
    if "expect" in e:
        ok = ok and actual == e["expect"]
        want.append("== %s" % e["expect"])
    if "min" in e:
        ok = ok and actual >= e["min"]
        want.append(">= %s" % e["min"])
    if "max" in e:
        ok = ok and actual <= e["max"]
        want.append("<= %s" % e["max"])
    if not want:
        raise ValueError("thiếu expect/min/max")
    return ok, " và ".join(want)


def measure(e, base):
    t = e.get("type")
    if t == "count_files":
        return len(glob.glob(os.path.join(base, e["glob"]), recursive=True))
    if t in ("json_len", "json_value"):
        with open(os.path.join(base, e["file"]), encoding="utf-8") as f:
            cur = json.load(f)
        if e.get("key"):
            cur = get_path(cur, e["key"])
        return len(cur) if t == "json_len" else cur
    if t == "file_size":
        return os.path.getsize(os.path.join(base, e["file"]))
    if t == "cmd_regex":
        r = subprocess.run(e["cmd"], shell=True, cwd=base, capture_output=True,
                           text=True, timeout=e.get("timeout", 600))
        m = re.search(e["regex"], r.stdout + r.stderr)
        if not m:
            raise ValueError("regex không khớp output của lệnh")
        g = m.group(1) if m.groups() else m.group(0)
        return int(g) if g.lstrip("-").isdigit() else g
    raise ValueError("kiểu check lạ: %r" % t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="agent_kit/invariants.json")
    ap.add_argument("--base", default=".")
    ap.add_argument("--group", help="chỉ chạy nhóm này (và nhóm 'always')")
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args()
    try:
        with open(a.file, encoding="utf-8") as f:
            checks = json.load(f)["checks"]
    except (OSError, ValueError, KeyError) as ex:
        print("FAIL  không đọc được %s: %s" % (a.file, ex))
        return 1
    passes = fails = skips = 0
    dirty = git_dirty(a.file)
    if dirty and not a.allow_dirty:
        print("FAIL  %s có thay đổi chưa commit. Chỉ NGƯỜI DÙNG được sửa file này rồi commit." % a.file)
        fails += 1
    elif dirty is None:
        print("WARN  không kiểm tra được git cho %s" % a.file)
    for e in checks:
        name, grp = e.get("name", "?"), e.get("group", "always")
        if a.group and grp not in (a.group, "always"):
            print("SKIP  [%s] %s (nhóm khác)" % (grp, name))
            skips += 1
            continue
        if e.get("skip"):
            print("SKIP  [%s] %s (%s)" % (grp, name, e["skip"]))
            skips += 1
            continue
        if any(isinstance(v, str) and ("TODO" in v or "<FILL" in v) for v in e.values()):
            print("FAIL  [%s] %s — chưa điền (còn TODO)" % (grp, name))
            fails += 1
            continue
        try:
            actual = measure(e, a.base)
            ok, want = judge(actual, e)
        except Exception as ex:  # báo lỗi to, không nuốt
            print("FAIL  [%s] %s — LỖI %s: %s" % (grp, name, type(ex).__name__, ex))
            fails += 1
            continue
        print("%s  [%s] %s — thực tế %s, mong đợi %s" % ("PASS" if ok else "FAIL", grp, name, actual, want))
        passes, fails = (passes + 1, fails) if ok else (passes, fails + 1)
    if passes == 0 and fails == 0:
        print("FAIL  không có check nào được chạy (kiểm tra --group và invariants.json)")
        fails += 1
    print("TỔNG: %d PASS, %d FAIL, %d SKIP" % (passes, fails, skips))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

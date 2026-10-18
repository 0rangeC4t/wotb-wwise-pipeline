#!/usr/bin/env python3
"""Chạy toàn bộ kiểm tra và sinh báo cáo. PHẦN BẰNG CHỨNG do script ghi (output lệnh
thật), agent chỉ điền các mục còn lại. Dùng: make_report.py --title "..." [--group X]
Kiểm tra báo cáo có bị sửa phần bằng chứng không:  make_report.py --verify <file.md>"""
import argparse
import datetime
import hashlib
import os
import re
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
START, END = "<!-- EVIDENCE-START -->", "<!-- EVIDENCE-END -->"


def run(cmd, timeout=1800):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as ex:
        return 99, "KHÔNG CHẠY ĐƯỢC %s: %s" % (cmd, ex)


def slug(s):
    s = unicodedata.normalize("NFKD", s.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()[:40] or "viec"


def block(title, code, out):
    return "### %s (exit %s)\n```\n%s\n```" % (title, code, out or "(không có output)")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(re.escape(START) + r"\n(.*?)\n" + re.escape(END), text, re.S)
    h = re.search(r"evidence_sha256: ([0-9a-f]{64})", text)
    if not m or not h:
        print("FAIL  không tìm thấy phần bằng chứng/mã băm trong %s" % path)
        return 1
    ok = sha(m.group(1)) == h.group(1)
    print("%s  phần bằng chứng %s" % ("OK" if ok else "FAIL", "nguyên vẹn" if ok else "ĐÃ BỊ SỬA"))
    return 0 if ok else 1


TEMPLATE = """# Báo cáo: {title}
- thời gian: {now}
- nhóm: {group}
- trạng thái tự động: **{status}**
- evidence_sha256: {digest}

## Bằng chứng do script sinh (agent KHÔNG được sửa phần này)
{start}
{evidence}
{end}

## Đã làm (1-3 dòng, agent điền)
TODO

## CHƯA kiểm chứng được (bắt buộc, không được ghi "không có")
TODO

## Bạn tự test thế này (3-5 bước cụ thể, kèm kết quả mong đợi)
TODO

## Commit
TODO (hash sau khi commit)
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title")
    ap.add_argument("--group")
    ap.add_argument("--scan-path", action="append", default=[])
    ap.add_argument("--roundtrip", nargs=2, metavar=("A_XML", "B_XML"))
    ap.add_argument("--allow")
    ap.add_argument("--outdir", default="reports")
    ap.add_argument("--verify")
    a = ap.parse_args()
    if a.verify:
        return verify(a.verify)
    if not a.title:
        ap.error("cần --title (hoặc --verify)")
    parts, ok = [], True
    for title, cmd in (("git rev-parse --short HEAD", ["git", "rev-parse", "--short", "HEAD"]),
                       ("git status --short", ["git", "status", "--short"]),
                       ("git diff --stat HEAD", ["git", "diff", "--stat", "HEAD"])):
        code, out = run(cmd)
        parts.append(block(title, code, out))
    c1 = [sys.executable, os.path.join(HERE, "check_invariants.py")] + (["--group", a.group] if a.group else [])
    c2 = [sys.executable, os.path.join(HERE, "scan_silent_failures.py")] + a.scan_path
    checks = [("check_invariants (số mốc)", c1), ("scan_silent_failures (lỗi câm, hardcode)", c2)]
    if a.roundtrip:
        c3 = [sys.executable, os.path.join(HERE, "roundtrip_diff.py")] + a.roundtrip + (["--allow", a.allow] if a.allow else [])
        checks.append(("roundtrip_diff (so với bank gốc)", c3))
    for title, cmd in checks:
        code, out = run(cmd)
        ok = ok and code == 0
        parts.append(block(title, code, out))
    evidence = "\n\n".join(parts)
    os.makedirs(a.outdir, exist_ok=True)
    now = datetime.datetime.now()
    stem = "%s_%s" % (now.strftime("%Y-%m-%d_%H%M"), slug(a.title))
    path, n = os.path.join(a.outdir, stem + ".md"), 2
    while os.path.exists(path):
        path = os.path.join(a.outdir, "%s-%d.md" % (stem, n))
        n += 1
    status = "PASS" if ok else "FAIL — KHÔNG được báo hoàn thành"
    with open(path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(title=a.title, now=now.strftime("%Y-%m-%d %H:%M"), group=a.group or "tất cả",
                                status=status, digest=sha(evidence), start=START, evidence=evidence, end=END))
    print("Báo cáo: %s" % path)
    print("Trạng thái tự động: %s" % status)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

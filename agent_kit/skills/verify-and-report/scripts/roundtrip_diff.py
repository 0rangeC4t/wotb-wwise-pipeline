#!/usr/bin/env python3
"""So CẤU TRÚC hai bản dump XML của wwiser (A = bank gốc, B = bank vừa build lại).
Đếm số lần xuất hiện của từng đường dẫn thẻ (a/b/c). Không so từng byte (GUID, thứ tự
có thể khác). Chỗ lệch nào KHÔNG nằm trong file --allow (do NGƯỜI DÙNG viết) => FAIL.
Lưu ý: cách này thô; cần thêm check riêng cho điểm RTPC, target của Action... nếu cần.
Bản dump phải do công cụ độc lập (wwiser) tạo ra, không phải parser tự viết."""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter


def histogram(path, include_attrs, ignore):
    c, stack = Counter(), []
    for ev, el in ET.iterparse(path, events=("start", "end")):
        if ev == "start":
            name = el.tag
            for a in include_attrs:
                if a in el.attrib:
                    name += "[%s=%s]" % (a, el.attrib[a])
            stack.append(name)
            p = "/".join(stack)
            if not any(r.search(p) for r in ignore):
                c[p] += 1
        else:
            stack.pop()
            el.clear()
    if not c:
        raise ValueError("%s: không đếm được phần tử nào" % path)
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--include-attr", action="append", default=[],
                    help="thuộc tính đưa vào tên đường dẫn (vd: type)")
    ap.add_argument("--ignore", action="append", default=[], help="regex đường dẫn bỏ qua")
    ap.add_argument("--allow", help="file JSON: danh sách regex đường dẫn được phép lệch")
    ap.add_argument("--max-lines", type=int, default=60)
    a = ap.parse_args()
    try:
        ign = [re.compile(x) for x in a.ignore]
        ha = histogram(a.a, a.include_attr, ign)
        hb = histogram(a.b, a.include_attr, ign)
        allow = []
        if a.allow:
            with open(a.allow, encoding="utf-8") as f:
                allow = [re.compile(x) for x in json.load(f)]
    except (OSError, ValueError, ET.ParseError, re.error) as ex:
        print("FAIL  %s: %s" % (type(ex).__name__, ex))
        return 2
    diffs = sorted(p for p in set(ha) | set(hb) if ha[p] != hb[p])
    bad = [p for p in diffs if not any(r.search(p) for r in allow)]
    print("A: %d phần tử / %d đường dẫn; B: %d phần tử / %d đường dẫn"
          % (sum(ha.values()), len(ha), sum(hb.values()), len(hb)))
    for p in bad[:a.max_lines]:
        print("LỆCH  %s  A=%d B=%d" % (p, ha[p], hb[p]))
    if len(bad) > a.max_lines:
        print("... và %d chỗ lệch nữa" % (len(bad) - a.max_lines))
    print("Lệch được phép: %d. Lệch KHÔNG được phép: %d." % (len(diffs) - len(bad), len(bad)))
    print("KẾT QUẢ: %s" % ("KHỚP" if not bad else "FAIL"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

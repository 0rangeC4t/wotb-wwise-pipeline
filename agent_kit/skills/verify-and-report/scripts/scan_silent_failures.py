#!/usr/bin/env python3
"""Quét lỗi câm trong code Python (R6) bằng phân tích cú pháp (AST).
Bắt: bare-except, swallowed-exception (except nuốt lỗi, không raise/log/gọi hàm),
empty-return-in-if (if chỉ để return []/{} — kiểu bug Fact #1), hardcoded-path
(/home/..., /mnt/...), syntax-error.
Code cũ đã có sẵn được ghi trong baseline; chỉ phát hiện MỚI mới làm FAIL (exit 1).
Chỉ NGƯỜI DÙNG được chạy --update-baseline."""
import argparse
import ast
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import git_dirty  # noqa: E402

SKIP_DIRS = {".git", "archive", "venv", ".venv", "__pycache__", "node_modules",
             "reports", "tools", "agent_kit"}
PATH_RE = re.compile(r"(?<![\w.])(/home/\w|/mnt/\w|/Users/\w|[A-Za-z]:\\)")


def swallows(body):
    for st in body:
        for n in ast.walk(st):
            if isinstance(n, (ast.Raise, ast.Call)):
                return False
    return True


def empty_collection(v):
    return ((isinstance(v, (ast.List, ast.Tuple, ast.Set)) and not v.elts)
            or (isinstance(v, ast.Dict) and not v.keys))


class Visitor(ast.NodeVisitor):
    def __init__(self, rel):
        self.rel, self.stack, self.found = rel, [], []
        self.count = Counter()

    def _fn(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = _fn

    def add(self, node, kind):
        fn = ".".join(self.stack) or "<module>"
        base = "%s|%s|%s" % (self.rel, kind, fn)
        self.count[base] += 1
        self.found.append(("%s|%d" % (base, self.count[base]), node.lineno, kind, fn))

    def visit_ExceptHandler(self, node):
        if node.type is None:
            self.add(node, "bare-except")
        elif swallows(node.body):
            self.add(node, "swallowed-exception")
        self.generic_visit(node)

    def visit_If(self, node):
        if (len(node.body) == 1 and isinstance(node.body[0], ast.Return)
                and empty_collection(node.body[0].value)):
            self.add(node, "empty-return-in-if")
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str) and PATH_RE.search(node.value):
            self.add(node, "hardcoded-path")


def scan(paths):
    files = []
    for root in paths:
        if os.path.isfile(root):
            files.append(root)
            continue
        for d, dirs, fs in os.walk(root):
            dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
            files += [os.path.join(d, f) for f in sorted(fs) if f.endswith(".py")]
    found = []
    for p in files:
        rel = os.path.relpath(p).replace(os.sep, "/")
        try:
            with open(p, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=p)
        except (SyntaxError, UnicodeDecodeError) as ex:
            found.append(("%s|syntax-error|-|1" % rel, getattr(ex, "lineno", 0) or 0, "syntax-error", str(ex)))
            continue
        v = Visitor(rel)
        v.visit(tree)
        found += v.found
    return files, found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--baseline", default="agent_kit/silent_baseline.txt")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true")
    a = ap.parse_args()
    paths = a.paths or [p for p in ("scripts", "core") if os.path.isdir(p)]
    if not paths:
        print("FAIL  không có thư mục để quét (truyền đường dẫn: scan_silent_failures.py <thư mục>)")
        return 1
    files, found = scan(paths)
    if not files:
        print("FAIL  không tìm thấy file .py nào trong %s" % paths)
        return 1
    if a.update_baseline:
        with open(a.baseline, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(k for k, *_ in found)) + "\n")
        print("Đã ghi baseline: %d mục. NGƯỜI DÙNG hãy xem lại rồi commit." % len(found))
        return 0
    base = set()
    if os.path.exists(a.baseline):
        with open(a.baseline, encoding="utf-8") as f:
            base = {x.strip() for x in f if x.strip()}
    else:
        print("WARN  chưa có baseline (%s): mọi phát hiện đều tính là MỚI" % a.baseline)
    fails = 0
    dirty = git_dirty(a.baseline)
    if dirty and not a.allow_dirty:
        print("FAIL  %s có thay đổi chưa commit. Chỉ NGƯỜI DÙNG được sửa baseline." % a.baseline)
        fails += 1
    new = [x for x in found if x[0] not in base]
    for key, line, kind, fn in sorted(new, key=lambda x: (x[0].split("|")[0], x[1])):
        print("FAIL  %s:%d  %s  (trong %s)" % (key.split("|")[0], line, kind, fn))
    fails += len(new)
    print("Đã quét %d file: %d phát hiện cũ (trong baseline), %d MỚI." % (len(files), len(found) - len(new), len(new)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

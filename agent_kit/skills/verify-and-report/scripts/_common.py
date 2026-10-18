"""Hàm dùng chung cho các script kiểm tra."""
import os
import subprocess


def git_dirty(path):
    """True nếu file có thay đổi chưa commit (hoặc chưa được git theo dõi).
    False nếu sạch. None nếu không dùng được git (khi đó script chỉ cảnh báo)."""
    if not os.path.exists(path):
        return None
    ap = os.path.abspath(path)
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", ap],
                           cwd=os.path.dirname(ap), capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return bool(r.stdout.strip())

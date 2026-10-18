#!/usr/bin/env bash
# Dùng: ./agent_kit/verify.sh "tên việc" [nhóm]
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
exec python3 agent_kit/skills/verify-and-report/scripts/make_report.py --title "$1" ${2:+--group "$2"}

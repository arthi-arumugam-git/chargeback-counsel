#!/usr/bin/env bash
# One-command offline showcase: seed -> triage queue -> deadlines -> brief -> dashboard -> tests.
set -euo pipefail
cd "$(dirname "$0")/.."
TODAY="${TODAY:-2026-11-08}"
python3 -m counsel.seed
echo "== Triage queue =="; python3 -m counsel.queue
echo "== Evidence deadlines ($TODAY) =="; python3 -m counsel.deadlines --today "$TODAY"
python3 -m counsel.brief --today "$TODAY" --out data/brief_late.md
python3 -m counsel.dashboard --today "$TODAY"
python3 -m pytest -q
echo "Showcase done: data/brief_late.md and data/dashboard.html"

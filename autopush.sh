#!/bin/sh
cd /Users/brandenwegner/Downloads/claude/dashboards || exit 1

# Snapshot the live dashboard HTML into docs/ for GitHub Pages
/usr/bin/curl -sf http://localhost:8787/ -o docs/index.html

/usr/bin/git add -A
/usr/bin/git diff --cached --quiet && exit 0
/usr/bin/git commit -m "Update dashboard snapshot $(date '+%Y-%m-%d %H:%M')"
/usr/bin/git push origin main

#!/bin/bash
# Regenerate the static dashboard snapshot and push to GitHub Pages.
# Designed to run headlessly from launchd every 30 minutes.

set -eu

DASHBOARD_DIR="/Users/brandenwegner/dashboards"
LOG_PREFIX="[dashboard-deploy $(date '+%Y-%m-%d %H:%M:%S')]"

cd "$DASHBOARD_DIR"

echo "$LOG_PREFIX Starting regeneration..."
python3 generate_static.py --no-open

git add docs/index.html

# If nothing changed, skip commit+push
if git diff --cached --quiet; then
    echo "$LOG_PREFIX No changes - skipping push."
    exit 0
fi

git commit -m "Update dashboard snapshot $(date '+%Y-%m-%d %H:%M')"
git push

echo "$LOG_PREFIX Pushed updated snapshot."

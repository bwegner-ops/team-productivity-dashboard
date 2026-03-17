#!/bin/sh
cd /Users/brandenwegner/Downloads/claude/dashboards || exit 1
/usr/bin/git add -A
/usr/bin/git diff --cached --quiet && exit 0
/usr/bin/git commit -m "auto: dashboard update"
/usr/bin/git push origin main

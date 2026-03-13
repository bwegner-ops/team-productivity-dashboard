#!/usr/bin/env python3
"""
Generate a static HTML snapshot of the Team Productivity Dashboard.

Fetches all data sources (Salesforce, Google Sheets, Snowflake JSON),
builds the dashboard HTML, tweaks it for static hosting (removes auto-refresh
and LIVE indicator), and writes it to site/index.html.
"""

import argparse
import os
import sys
import re
import webbrowser
from datetime import datetime

# Import everything from the dashboard module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
dash = import_module("case-completion-dashboard")

SITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")


def fetch_all_data():
    """Fetch data from all sources, mirroring the live server's logic."""
    print("Fetching DRI data from Google Sheets...")
    dri_data = None
    try:
        rows = dash.fetch_dri_data()
        if rows:
            dri_data = dash.parse_dri_data(rows)
            print(f"  DRI: {dri_data['totalResolved']} resolved, {dri_data['totalSubmitted']} submitted")
    except Exception as e:
        print(f"  Warning: DRI fetch failed: {e}")

    print("Fetching Evasion data from Google Sheets...")
    evasion_data = None
    try:
        rows = dash.fetch_evasion_data()
        if rows:
            evasion_data = dash.parse_evasion_data(rows)
            print(f"  Evasion: {evasion_data['totalActioned']} actioned, {evasion_data['totalReviews']} reviews")
    except Exception as e:
        print(f"  Warning: Evasion fetch failed: {e}")

    print("Fetching Salesforce report data...")
    token, instance = dash.get_sf_auth()

    raw_today = dash.fetch_report(token, instance)
    parsed = dash.parse_report(raw_today)
    print(f"  Today: {parsed['totalCases']} cases")

    monthly_filter = {
        "column": "CLOSED_DATEONLY",
        "durationValue": "THIS_MONTH",
        "startDate": None,
        "endDate": None,
    }
    raw_monthly = dash.fetch_report(token, instance, date_filter=monthly_filter)
    monthly, people = dash.parse_monthly(raw_monthly)
    print(f"  Month: {sum(d['count'] for d in monthly)} cases")

    queue = dash.fetch_queue_counts(token, instance)
    peak = dash.fetch_peak_queue_total(token, instance)
    print(f"  Queue: {sum(queue.values())} personal, {peak} total")

    print("Fetching Bankruptcy data from Google Sheets...")
    bk_data = None
    try:
        rows = dash.fetch_bk_data()
        if rows:
            bk_data = dash.parse_bk_data(rows)
            if bk_data:
                print(f"  BK: {bk_data.get('grandTotal', 0)} total cases")
    except Exception as e:
        print(f"  Warning: BK fetch failed: {e}")

    return parsed, monthly, people, queue, peak, dri_data, evasion_data, bk_data


def make_static(html):
    """Transform live dashboard HTML into a static snapshot."""
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Remove meta refresh tag
    html = re.sub(
        r'<meta http-equiv="refresh"[^>]*>\n?',
        '',
        html,
    )

    # Replace LIVE indicator + refresh note with snapshot banner
    html = re.sub(
        r'<div class="live">LIVE</div>\s*'
        r'<div style="margin-top:4px">Updated [^<]*</div>\s*'
        r'<div>Refreshes every [^<]*</div>',
        f'<div style="color:var(--accent);font-weight:500">SNAPSHOT</div>\n'
        f'    <div style="margin-top:4px">Generated {timestamp}</div>',
        html,
    )

    # Remove the .live CSS animation (no longer needed)
    html = re.sub(
        r'\.meta \.live\s*\{[^}]*\}\s*'
        r'\.meta \.live::before\s*\{[^}]*\}\s*'
        r'@keyframes pulse\s*\{[^}]*\{[^}]*\}[^}]*\}',
        '',
        html,
    )

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate static dashboard snapshot")
    parser.add_argument("--no-open", action="store_true", help="Skip opening browser (for cron/headless use)")
    args = parser.parse_args()

    os.makedirs(SITE_DIR, exist_ok=True)

    parsed, monthly, people, queue, peak, dri_data, evasion_data, bk_data = fetch_all_data()

    print("\nBuilding HTML...")
    html = dash.build_html(parsed, monthly, people, queue, peak, dri_data, evasion_data, bk_data=bk_data)

    html = make_static(html)

    out_path = os.path.join(SITE_DIR, "index.html")
    with open(out_path, "w") as f:
        f.write(html)

    print(f"\nWrote {len(html):,} bytes to {out_path}")
    if not args.no_open:
        webbrowser.open(f"file://{out_path}")


if __name__ == "__main__":
    main()

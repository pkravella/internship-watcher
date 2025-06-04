"""
watcher.py
~~~~~~~~~~
Main orchestration script:
  1. Fetch README.md from GitHub
  2. Parse internship rows
  3. Diff against snapshot
  4. Email any new rows
  5. Update snapshot
"""
from __future__ import annotations

import os
import time
import requests
import dotenv
from rich import print, box
from rich.console import Console
from rich.table import Table
from typing import List, Dict

import parser           # local modules
import storage
import notifier

## ------------------------------------------------------------------ ##
## Configuration
## ------------------------------------------------------------------ ##

GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/"
    "vanshb03/Summer2026-Internships/main/README.md"
)
ETAG_FILE = ".etag"        # cache to avoid re‑downloading unchanged file
TIMEOUT   = 30             # seconds for HTTP request

console = Console()

## ------------------------------------------------------------------ ##
## Helpers
## ------------------------------------------------------------------ ##

def _conditional_get(url: str) -> str | None:
    """Return README contents or None if it hasn't changed (HTTP 304)."""
    headers = {}
    if os.path.exists(ETAG_FILE):
        headers["If-None-Match"] = open(ETAG_FILE).read().strip()

    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    if r.status_code == 304:
        console.log("[cyan]No change on GitHub (HTTP 304) – exiting[/]")
        return None
    r.raise_for_status()

    etag = r.headers.get("ETag")
    if etag:
        with open(ETAG_FILE, "w") as fp:
            fp.write(etag)
    return r.text

def _diff(
    current: List[Dict[str, str]],
    previous: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    prev_key = {(r["company"], r["role"]): r for r in previous}
    return [
        r for r in current
        if (r["company"], r["role"]) not in prev_key
    ]

def _pretty_print(rows: List[Dict[str, str]]) -> None:
    if not rows:
        return
    tbl = Table(title="New internships", box=box.MINIMAL_DOUBLE_HEAD)
    tbl.add_column("Company", style="bold")
    tbl.add_column("Role")
    tbl.add_column("Link", overflow="fold")
    for r in rows:
        tbl.add_row(r["company"], r["role"], r["link"])
    console.print(tbl)

## ------------------------------------------------------------------ ##
## Main
## ------------------------------------------------------------------ ##

def main() -> None:
    dotenv.load_dotenv()            # pick up .env secrets

    md_text = _conditional_get(GITHUB_RAW_URL)
    if md_text is None:
        return                      # nothing new

    # Parse & diff
    current_rows  = parser.parse(md_text)
    previous_rows = storage.load_snapshot()
    new_rows      = _diff(current_rows, previous_rows)

    if new_rows:
        _pretty_print(new_rows)
        notifier.notify(new_rows)
        storage.save_snapshot(current_rows)
        console.log(f"[green]Emailed {len(new_rows)} new row(s) and updated snapshot[/]")
    else:
        console.log("[yellow]README changed, but no new listings detected[/]")

if __name__ == "__main__":
    start = time.perf_counter()
    try:
        main()
    finally:
        console.log(f"Done in {time.perf_counter() - start:.2f}s")

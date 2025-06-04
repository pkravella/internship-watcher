"""
storage.py
~~~~~~~~~~
Tiny JSON‑file “database” to remember previously seen rows.
"""
from __future__ import annotations

import json
import pathlib
from typing import List, Dict

_DB_PATH = pathlib.Path("snapshot.json")

def load_snapshot() -> List[Dict[str, str]]:
    if _DB_PATH.exists():
        return json.loads(_DB_PATH.read_text())
    return []

def save_snapshot(rows: List[Dict[str, str]]) -> None:
    _DB_PATH.write_text(json.dumps(rows, indent=2, sort_keys=True))

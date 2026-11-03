#!/usr/bin/env python3
"""Download every dataset in datasets/manifest.json and check size and sha256.

Run before a batch of runs: if a pinned file changed or disappeared, the prompts are no longer valid.
Datasets with status "todo" are skipped and listed.

Usage:  python3 scripts/verify_data.py
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
manifest = json.loads((ROOT / "datasets/manifest.json").read_text())
bad = False
for name, ds in manifest.items():
    if name.startswith("_"):
        continue
    if ds["status"] != "verified":
        print(f"SKIP  {name}: status {ds['status']}")
        continue
    with urllib.request.urlopen(ds["url"], timeout=120) as r:
        data = r.read()
    digest = hashlib.sha256(data).hexdigest()
    ok = digest == ds["sha256"] and len(data) == ds["bytes"]
    bad |= not ok
    print(f"{'OK  ' if ok else 'FAIL'}  {name}: {len(data)} bytes, sha256 {digest[:16]}")
sys.exit(1 if bad else 0)

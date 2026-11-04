#!/usr/bin/env python3
"""Point the E4/E5 data URLs at a commit of the public data-snapshot repository, check the files, rebuild prompts.

  python3 scripts/pin_data_repo.py denisseram/dataset-snapshots <commit-sha>

Downloads each file from https://raw.githubusercontent.com/<repo>/<sha>/<file>, checks that size and sha256
are the ones recorded in datasets/manifest.json (the bytes must not change, only their address), writes the
new URLs and runs scripts/build_prompts.py.
"""
import hashlib
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = {"ubuntu_releases": "ubuntu.csv", "geosphere_wien_10min": "geosphere_wien_10min_2020-2024.csv"}

if len(sys.argv) != 3 or "/" not in sys.argv[1] or len(sys.argv[2]) != 40:
    sys.exit(__doc__)
repo, sha = sys.argv[1], sys.argv[2]
if "time-i-gram" in repo.lower() or "eval" in repo.lower():
    sys.exit("The repository name must not reveal the evaluation (it appears in every prompt).")

path = ROOT / "datasets/manifest.json"
manifest = json.loads(path.read_text())
for key, name in FILES.items():
    url = f"https://raw.githubusercontent.com/{repo}/{sha}/{name}"
    with urllib.request.urlopen(url, timeout=120) as r:
        data = r.read()
        cors = r.headers.get("access-control-allow-origin")
    digest = hashlib.sha256(data).hexdigest()
    entry = manifest[key]
    if digest != entry["sha256"] or len(data) != entry["bytes"]:
        sys.exit(f"{name}: {len(data)} bytes, sha256 {digest[:16]}; expected {entry['bytes']} bytes, "
                 f"{entry['sha256'][:16]}. Not changed.")
    if cors != "*":
        sys.exit(f"{name}: the server does not allow browser access (CORS); D3, Vega-Lite and time-i-gram could not load it.")
    entry["url"], entry["status"] = url, "verified"
    print(f"OK  {name}: {len(data)} bytes, sha256 {digest[:16]}, CORS allowed")
path.write_text(json.dumps(manifest, indent=2) + "\n")
sys.exit(subprocess.run([sys.executable, str(ROOT / "scripts/build_prompts.py")]).returncode)

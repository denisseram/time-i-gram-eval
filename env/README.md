# Run environment: setup on your computer

Everything the agents use runs inside one Docker image (`env/Dockerfile`): R with ggtime, Node 22,
Chromium, the `render` command and Claude Code, all with pinned versions. Each run gets a new container
whose only file is `prompt.md`. This repository never goes into the image.

## 1. Install (once)

1. **Docker Desktop**: https://www.docker.com/products/docker-desktop. Open it; in
   *Settings → Resources* give it at least 4 CPUs, 8 GB memory and 40 GB disk.
2. **Node.js** (only to create the login token below): `brew install node`, or the installer from
   https://nodejs.org.
3. **Claude Code on your computer** (only for the token): `npm install -g @anthropic-ai/claude-code`
4. **Python 3**: `python3 --version` should print 3.9 or newer (macOS offers to install it the first time).

## 2. Credential (once)

The agents use your Claude plan through a long-lived token:

```bash
claude setup-token              # opens the browser; log in with the account that has the Pro plan
```

It prints a token. In the repository root, create a file named `.env` (it is in `.gitignore`, so it is never
committed) with one line:

```
CLAUDE_CODE_OAUTH_TOKEN=paste-the-token-here
```

Do **not** also set `ANTHROPIC_API_KEY` (in `.env` or in your shell): Claude Code would use it instead of
your plan and bill the API. The runner refuses to start if both are set. To use the API instead of the plan,
put only `ANTHROPIC_API_KEY=...` in `.env`.

## 3. Build the image (once, and again only if env/ changes)

```bash
cd ~/Documents/time-i-gram-eval
docker build -t tig-eval:1 env/
```

The first build downloads and installs R packages, Chromium and Claude Code: allow 20–40 minutes. At the
end it prints every installed version (also saved in the image as `/opt/versions.txt`).

## 4. Smoke test

```bash
scripts/tests/smoke_render.sh
```

It renders one demo deliverable per tool with the official `render` command (the ggtime one runs real R
code), copies the screenshots to `results/smoke/`, and asks Claude Code for a one-word answer with your
token. Everything should say OK; look at the four screenshots. Then:

```bash
python3 scripts/runner.py check
```

lists what is still missing before the runs (data pinned, freeze tag, schedule).

## Notes

- **Apple silicon:** the image is built for arm64 natively. R packages without arm64 binaries are compiled
  during the build (slower, same versions).
- **Versions to report:** `/opt/versions.txt` (also copied into every run's `meta.json`). If the ggtime
  version differs from the one in `tools/ggtime.md`, update the tool section and rebuild the prompts before
  freezing.
- **Disk:** each run keeps its transcript and outputs in `runs/`; files over 2 MB the agent downloaded (e.g.
  data copies) are listed in `meta.json` but not kept.

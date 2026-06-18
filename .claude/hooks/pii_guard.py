#!/usr/bin/env python3
"""PreToolUse PII guard — repo-scoped, committed.

Blocks client chart data from entering the TRACKED repo: client charts must live in
`.private/charts/`, never in the public, git-tracked `charts/` (which holds only public
fixtures). Catches the two real leak paths:
  1. Write/Edit creating a non-fixture dir under `charts/`  — caught at the door.
  2. `git add`/`git commit` with a non-fixture `charts/` path or birth-data content staged.

Mechanism: read the hook JSON from stdin; exit 2 + stderr = BLOCK; exit 0 = allow.
This protects the repo and any clone/agent working here, independent of whether the agent
read the docs (instructions != enforcement).
"""
import sys, json, subprocess, re, os

# public, non-PII fixtures allowed to live in tracked charts/
ALLOW = {
    "trump_19460614_105400_jamaica_ny",
    "trump_19460614_105400_jamaica_ny_renderer",
    "trump_tz_derive_smoke",
    "AGENTS.md", "README.md",
}
# birth-data shaped content (a real date on a chart datetime key)
PII_CONTENT = re.compile(r"(utc_datetime|local_datetime)\s*:\s*\d{4}-\d{2}-\d{2}", re.I)


def block(msg):
    sys.stderr.write("PII GUARD (blocked): " + msg + "\n")
    sys.exit(2)


def public_chart_top(path):
    """Return the offending top-level name if `path` is a non-fixture under tracked charts/,
    else None. `.private/charts/...` is always allowed."""
    p = path.replace("\\", "/")
    if ".private/" in p:
        return None
    i = p.find("charts/")
    if i < 0:
        return None
    rest = p[i + len("charts/"):]
    if not rest:
        return None
    top = rest.split("/")[0]
    if top in ALLOW:
        return None
    return top


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    # 1) Write/Edit into public charts/ non-fixture
    if tool in ("Write", "Edit", "MultiEdit"):
        fp = ti.get("file_path") or ti.get("path") or ""
        top = public_chart_top(fp)
        if top:
            block(f"writing client chart '{top}' into tracked charts/. "
                  f"Client chart data goes to .private/charts/, never public charts/.")
        sys.exit(0)

    # 2) git add / git commit — scan what is (about to be) staged
    if tool == "Bash":
        cmd = ti.get("command", "") or ""
        if not re.search(r"\bgit\s+(commit|add)\b", cmd):
            sys.exit(0)
        try:
            staged = subprocess.run(["git", "diff", "--cached", "--name-only"],
                                    capture_output=True, text=True).stdout
        except Exception:
            staged = ""
        bad = sorted({f"charts/{public_chart_top(f)}" for f in staged.splitlines()
                      if public_chart_top(f)})
        if bad:
            block("staged client chart(s) in tracked charts/: " + ", ".join(bad)
                  + " — move to .private/charts/ before committing.")
        # birth-data content in any staged non-fixture, non-private file
        for f in staged.splitlines():
            fp = f.replace("\\", "/")
            if ".private/" in fp or fp.split("/")[-1] in ALLOW:
                continue
            if any(fp.endswith(x) or f"/{x}/" in f"/{fp}/" for x in ALLOW):
                continue
            try:
                d = subprocess.run(["git", "diff", "--cached", "--", f],
                                   capture_output=True, text=True).stdout
            except Exception:
                d = ""
            if PII_CONTENT.search(d):
                block(f"staged file '{f}' contains birth-data (datetime key with a real date) "
                      f"— looks like client PII; keep it in .private/.")
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()

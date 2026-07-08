"""
port_guides.py – mirror the upstream repo's published guides into this app.

The source of truth is the **main branch** of the sibling ResearchGuides repo,
read directly through git — so it does not matter which branch happens to be
checked out over there, and nothing in that repo's working tree is touched.

Per run:

  1. list the guide directories committed under research-guides/ on `main`
     (override the ref with --ref),
  2. drop the authoring template (and anything else in guides.exclude),
  3. extract each remaining guide's committed files from main into this repo's
     research-guides/<slug>/ — main commits the rendered HTML and _files/, so
     there is no quarto render step and no Stata/Julia/R dependency,
  4. delete any research-guides/<slug>/ here that is no longer on main, so the
     local set is an exact mirror, then
  5. run tools/build.py --clean to publish temp/ and guides_manifest.json.

Because selection comes from main, the only thing you maintain by hand is the
short guides.exclude list (the template). Switching branches in the upstream
repo, renaming a guide, or adding one all flow through automatically.

Usage
-----
    python tools/port_guides.py                 # mirror main -> research-guides -> temp
    python tools/port_guides.py --ref origin/main
    python tools/port_guides.py --only logit-probit   # one guide (repeatable)
    python tools/port_guides.py --dry-run
    python tools/port_guides.py --list
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build as build_mod
from tools import consult as consult_mod
from tools.build import load_exclusions

# The two repos are siblings: …/StatLab/statlab and …/StatLab/ResearchGuides.
DEFAULT_UPSTREAM = ROOT.parent / "ResearchGuides"
UPSTREAM_SUBDIR = "research-guides"
DEFAULT_REF = "main"
DEST_GUIDES = ROOT / "research-guides"

# Rendered output only — never sources, render caches, or per-guide scratch.
_COPY_IGNORE = shutil.ignore_patterns(
    "*.qmd", "*.Rmd", "*.rmarkdown", "*.sh",
    "_freeze", ".quarto", ".git*",
    "renv", "renv.lock", ".Rproj.user",
    "archive", "src", "notes-to-self*",
    ".DS_Store", "verify_*",
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True,
    )


def is_git_repo(repo: Path) -> bool:
    return repo.is_dir() and _git(repo, "rev-parse", "--git-dir").returncode == 0


def ref_exists(repo: Path, ref: str) -> bool:
    return _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode == 0


def catalog(repo: Path, ref: str) -> list[str]:
    """Guide directory names committed under research-guides/ on `ref`."""
    proc = _git(repo, "ls-tree", "-d", "--name-only", f"{ref}:{UPSTREAM_SUBDIR}")
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"cannot read {ref}:{UPSTREAM_SUBDIR}")
    return sorted(
        name for name in proc.stdout.splitlines()
        if name and not name.startswith(".") and name not in build_mod.LEGACY_DIRS
    )


def extract_guide(repo: Path, ref: str, slug: str, dest_dir: Path) -> None:
    """Replace dest_dir with the committed contents of <ref>:research-guides/<slug>."""
    archive = subprocess.run(
        ["git", "-C", str(repo), "archive", "--format=tar", f"{ref}:{UPSTREAM_SUBDIR}/{slug}"],
        capture_output=True,
    )
    if archive.returncode != 0:
        raise RuntimeError(archive.stderr.decode(errors="replace").strip())
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["tar", "-x", "-C", td], input=archive.stdout, check=True)
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        shutil.copytree(td, dest_dir, ignore=_COPY_IGNORE)


def normalize_main_html(dest_dir: Path, slug: str) -> tuple[bool, str]:
    """Ensure dest_dir/<slug>.html exists (build.py and app.py assume that name)."""
    expected = dest_dir / f"{slug}.html"
    if expected.is_file():
        return True, ""
    candidates = sorted(p.name for p in dest_dir.glob("*.html"))
    if len(candidates) == 1:
        shutil.copy(dest_dir / candidates[0], expected)
        return True, f"normalized {candidates[0]} -> {slug}.html"
    if not candidates:
        return False, "no HTML committed on main for this guide"
    return False, f"ambiguous main HTML — none named {slug}.html among {candidates}"


def sync_dest(keep: set[str], *, dry_run: bool) -> list[str]:
    """Remove research-guides/<slug>/ here that is not in `keep` (the mirror set)."""
    removed = []
    if not DEST_GUIDES.is_dir():
        return removed
    for entry in sorted(DEST_GUIDES.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if entry.name in build_mod.LEGACY_DIRS or entry.name in keep:
            continue
        removed.append(entry.name)
        if not dry_run:
            shutil.rmtree(entry)
    return removed


def port(
    upstream: Path = DEFAULT_UPSTREAM,
    *,
    ref: str = DEFAULT_REF,
    only: list[str] | None = None,
    dry_run: bool = False,
) -> int:
    upstream = upstream.resolve()
    if not is_git_repo(upstream):
        print(f"error: not a git repo: {upstream}\n"
              f"       (clone ResearchGuides next to this repo, or pass --upstream)", file=sys.stderr)
        return 1
    if not ref_exists(upstream, ref):
        print(f"error: ref '{ref}' not found in {upstream} (try --ref origin/main)", file=sys.stderr)
        return 1

    try:
        cat = catalog(upstream, ref)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    excluded = load_exclusions(build_mod.DEFAULT_EXCLUDE_FILE) if build_mod.DEFAULT_EXCLUDE_FILE.is_file() else set()
    unmatched = sorted(slug for slug in excluded if slug not in cat)
    if unmatched:
        print(
            f"error: guides.exclude entries are not on {ref}:\n"
            + "".join(f"  - {slug}\n" for slug in unmatched)
            + "Remove them — selection now comes from the upstream main branch.",
            file=sys.stderr,
        )
        return 1

    if only:
        missing = sorted(s for s in only if s not in cat)
        if missing:
            print(f"error: not on {ref}: {', '.join(missing)}", file=sys.stderr)
            print(f"       available: {', '.join(cat)}", file=sys.stderr)
            return 1
        selected = [s for s in cat if s in set(only)]
    else:
        selected = [s for s in cat if s not in excluded]

    if dry_run:
        for slug in selected:
            print(f"  would port: {slug}")
        if not only:
            for slug in sorted(set(cat) - set(selected)):
                print(f"  excluded:   {slug}")
            # --only never prunes; only a full mirror run removes orphans.
            for name in sync_dest(set(selected), dry_run=True):
                print(f"  would remove (not on {ref}): {name}")
        print(f"dry run: {len(selected)} guide(s) from {ref}; build.py would publish temp/ afterwards")
        return 0

    results: list[tuple[str, str, str]] = []
    for slug in selected:
        try:
            extract_guide(upstream, ref, slug, DEST_GUIDES / slug)
        except Exception as exc:
            results.append((slug, "FAILED (extract)", str(exc)))
            continue
        ok, detail = normalize_main_html(DEST_GUIDES / slug, slug)
        if not ok:
            shutil.rmtree(DEST_GUIDES / slug, ignore_errors=True)
            results.append((slug, "FAILED (normalize)", detail))
            continue
        results.append((slug, "ported", detail))

    # Mirror: a full run drops local guides no longer on the ref. A single-guide
    # port (--only) touches just that guide and never prunes the existing mirror.
    if only:
        removed = []
    else:
        ported_ok = {s for s, status, _ in results if status == "ported"}
        removed = sync_dest(ported_ok, dry_run=False)

    print("\n--- port summary " + "-" * 43)
    failures = 0
    for slug, status, detail in results:
        if status.startswith("FAILED"):
            failures += 1
        line = f"  {slug:<28} {status}"
        print(line if not detail else f"{line}\n      {detail}")
    for name in removed:
        print(f"  {name:<28} removed (not on {ref})")
    print(f"{len(results) - failures} ported, {failures} failed, {len(removed)} removed\n")

    print("running tools/build.py --clean ...")
    build_rc = build_mod.build(clean=True)
    # Now that the manifest is fresh, recount authored guides per consultant and
    # post the counts to their profiles. Advisory (always 0) — a stale count
    # never fails a port.
    print("recounting guides per consultant ...")
    consult_mod.sync()
    return 1 if failures or build_rc else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mirror the upstream repo's main-branch guides into the Flask app.",
    )
    parser.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM,
                        help="upstream git repo (default: ../ResearchGuides)")
    parser.add_argument("--ref", default=DEFAULT_REF,
                        help="git ref to read guides from (default: main)")
    parser.add_argument("--only", action="append", metavar="SLUG",
                        help="port only this guide (repeatable); does not prune the rest")
    parser.add_argument("--dry-run", action="store_true",
                        help="show what would be ported/removed; change nothing")
    parser.add_argument("--list", action="store_true",
                        help="list the guides on the ref and their exclusion status")
    args = parser.parse_args(argv)

    if args.list:
        upstream = args.upstream.resolve()
        if not is_git_repo(upstream) or not ref_exists(upstream, args.ref):
            print(f"error: cannot read {args.ref} in {upstream}", file=sys.stderr)
            return 1
        excluded = load_exclusions(build_mod.DEFAULT_EXCLUDE_FILE) if build_mod.DEFAULT_EXCLUDE_FILE.is_file() else set()
        for slug in catalog(upstream, args.ref):
            print(f"  {slug}{'   [excluded]' if slug in excluded else ''}")
        return 0

    return port(args.upstream, ref=args.ref, only=args.only, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

"""
port_guides.py – render research guides in the upstream ResearchGuides repo
and port them into the Flask app.

Pipeline, per guide:

  1. `quarto render` each top-level .qmd in the upstream guide directory
     (skipped with --no-render, for guides whose committed HTML is current),
  2. copy the rendered output — HTML, `_files/`, data; never .qmd/.Rmd
     sources — into research-guides/<slug>/ in this repo, replacing what's
     there,
  3. normalize the main HTML file to <slug>.html (build.py and app.py both
     assume that name); a guide with several candidate HTML files and no
     <slug>.html fails loudly instead of guessing,

then tools/build.py runs once to publish temp/ and guides_manifest.json.

Guide selection comes from guides.exclude — the same file build.py reads.
This script validates every exclusion entry against the upstream catalog
(the full set of guides), so typos fail here even though an entry excluded
before porting never appears in this repo's research-guides/.

Render failures don't abort the run: each failed guide is reported in a
summary table at the end and the script exits non-zero.

Usage
-----
    python tools/port_guides.py                        # render + port every non-excluded guide
    python tools/port_guides.py --only standard-errors # one guide (repeatable)
    python tools/port_guides.py --only standard-errors --no-render
    python tools/port_guides.py --dry-run
    python tools/port_guides.py --list
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import build as build_mod
from tools.build import load_exclusions

# The two repos are siblings: …/StatLab/statlab and …/StatLab/ResearchGuides.
DEFAULT_UPSTREAM = ROOT.parent / "ResearchGuides" / "research-guides"
DEST_GUIDES = ROOT / "research-guides"

# Mirrors the legacy deploy workflow's rsync excludes: rendered output only,
# no sources, no render caches. verify_* are cross-lang-verify scratch files.
_COPY_IGNORE = shutil.ignore_patterns(
    "*.qmd", "*.Rmd", "*.rmarkdown",
    "_freeze", ".quarto", ".git*",
    "renv", "renv.lock", ".Rproj.user",
    ".DS_Store", "verify_*",
)

_STATA_BINARIES = ("stata-mp", "stata-se", "stata", "StataMP", "StataSE")


def upstream_slugs(upstream: Path) -> list[str]:
    return sorted(
        p.name for p in upstream.iterdir()
        if p.is_dir() and not p.name.startswith(".") and p.name not in build_mod.LEGACY_DIRS
    )


def guide_uses_stata(guide_dir: Path) -> bool:
    for qmd in guide_dir.glob("*.qmd"):
        if "{stata" in qmd.read_text(encoding="utf-8", errors="replace"):
            return True
    return False


def render_guide(guide_dir: Path) -> tuple[bool, str]:
    """Render every top-level .qmd in guide_dir. Returns (ok, detail)."""
    qmds = sorted(guide_dir.glob("*.qmd"))
    if not qmds:
        return False, "no .qmd file to render"
    for qmd in qmds:
        proc = subprocess.run(
            ["quarto", "render", qmd.name],
            cwd=guide_dir,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            tail = "\n".join((proc.stderr or proc.stdout).strip().splitlines()[-8:])
            return False, f"quarto render {qmd.name} failed:\n{tail}"
    return True, f"rendered {', '.join(q.name for q in qmds)}"


def copy_guide(src_dir: Path, dest_dir: Path) -> None:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(src_dir, dest_dir, ignore=_COPY_IGNORE)


def normalize_main_html(dest_dir: Path, slug: str) -> tuple[bool, str]:
    """Ensure dest_dir/<slug>.html exists; copy the sole candidate if needed.

    The original file is kept — its relative asset paths (<name>_files/)
    still resolve because the asset directories are copied under their
    original names.
    """
    expected = dest_dir / f"{slug}.html"
    if expected.is_file():
        return True, ""
    candidates = sorted(p.name for p in dest_dir.glob("*.html"))
    if len(candidates) == 1:
        shutil.copy(dest_dir / candidates[0], expected)
        return True, f"normalized {candidates[0]} -> {slug}.html"
    if not candidates:
        return False, "render produced no HTML file"
    return False, (
        f"ambiguous main HTML — none named {slug}.html among {candidates}; "
        "rename the upstream .qmd output so exactly one candidate remains"
    )


def preflight(*, no_render: bool, slugs_using_stata: list[str]) -> bool:
    """Report toolchain availability. Returns False only on hard blockers."""
    if not no_render and shutil.which("quarto") is None:
        print("error: quarto not found on PATH — required to render (or use --no-render)", file=sys.stderr)
        return False
    if not no_render:
        if shutil.which("julia") is None:
            print("note: julia not on PATH — guides with Julia chunks will fail to render")
        if not any(shutil.which(b) for b in _STATA_BINARIES):
            if slugs_using_stata:
                print("note: Stata not on PATH — these guides use Stata chunks and will likely fail:")
                for slug in slugs_using_stata:
                    print(f"        {slug}")
            else:
                print("note: Stata not on PATH (no selected guide uses Stata chunks)")
    return True


def port(
    upstream: Path = DEFAULT_UPSTREAM,
    *,
    only: list[str] | None = None,
    no_render: bool = False,
    dry_run: bool = False,
) -> int:
    upstream = upstream.resolve()
    if not upstream.is_dir():
        print(f"error: upstream guides directory not found: {upstream}\n"
              f"       (clone ResearchGuides next to this repo, or pass --upstream)", file=sys.stderr)
        return 1

    catalog = upstream_slugs(upstream)
    excluded = load_exclusions(build_mod.DEFAULT_EXCLUDE_FILE) if build_mod.DEFAULT_EXCLUDE_FILE.is_file() else set()

    # Strict typo check: the upstream catalog is the authoritative guide list.
    unmatched = sorted(slug for slug in excluded if slug not in catalog)
    if unmatched:
        print(
            "error: guides.exclude entries match no upstream guide:\n"
            + "".join(f"  - {slug}\n" for slug in unmatched)
            + "Fix the typo or remove the entry (was the guide renamed?).",
            file=sys.stderr,
        )
        return 1

    if only:
        missing = sorted(s for s in only if s not in catalog)
        if missing:
            print(f"error: not in upstream catalog: {', '.join(missing)}", file=sys.stderr)
            print(f"       available: {', '.join(catalog)}", file=sys.stderr)
            return 1
        blocked = sorted(s for s in only if s in excluded)
        if blocked:
            print(f"error: excluded by guides.exclude: {', '.join(blocked)} — "
                  "remove the entry first if this guide should ship", file=sys.stderr)
            return 1
        selected = list(dict.fromkeys(only))
    else:
        selected = [s for s in catalog if s not in excluded]

    stata_guides = [s for s in selected if guide_uses_stata(upstream / s)]
    if not preflight(no_render=no_render, slugs_using_stata=stata_guides):
        return 1

    if dry_run:
        for slug in selected:
            action = "copy" if no_render else "render + copy"
            print(f"  would {action}: {slug}")
        skipped = sorted(set(catalog) - set(selected))
        if skipped and not only:
            print(f"  excluded: {', '.join(skipped)}")
        print(f"dry run: {len(selected)} guide(s); tools/build.py would publish to temp/ afterwards")
        return 0

    results: list[tuple[str, str, str]] = []  # slug, status, detail

    for slug in selected:
        src_dir = upstream / slug

        if not no_render:
            ok, detail = render_guide(src_dir)
            if not ok:
                results.append((slug, "FAILED (render)", detail))
                continue

        dest_dir = DEST_GUIDES / slug
        copy_guide(src_dir, dest_dir)

        ok, detail = normalize_main_html(dest_dir, slug)
        if not ok:
            shutil.rmtree(dest_dir)  # don't leave a half-ported guide behind
            results.append((slug, "FAILED (normalize)", detail))
            continue

        results.append((slug, "ported", detail))

    print("\n--- port summary " + "-" * 43)
    failures = 0
    for slug, status, detail in results:
        if status.startswith("FAILED"):
            failures += 1
        line = f"  {slug:<34} {status}"
        print(line if not detail else f"{line}\n      {detail}")
    print(f"{len(results) - failures} ported, {failures} failed\n")

    print("running tools/build.py ...")
    build_rc = build_mod.build()

    return 1 if failures or build_rc else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render upstream research guides and port them into the Flask app.",
    )
    parser.add_argument(
        "--upstream", type=Path, default=DEFAULT_UPSTREAM,
        help="upstream guides directory (default: ../ResearchGuides/research-guides)",
    )
    parser.add_argument(
        "--only", action="append", metavar="SLUG",
        help="port only this guide (repeatable)",
    )
    parser.add_argument(
        "--no-render", action="store_true",
        help="skip quarto; copy already-rendered upstream HTML as-is",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="show what would happen; render, copy, and build nothing",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="list the upstream guide catalog and exclusion status",
    )
    args = parser.parse_args(argv)

    if args.list:
        upstream = args.upstream.resolve()
        if not upstream.is_dir():
            print(f"error: upstream guides directory not found: {upstream}", file=sys.stderr)
            return 1
        excluded = load_exclusions(build_mod.DEFAULT_EXCLUDE_FILE) if build_mod.DEFAULT_EXCLUDE_FILE.is_file() else set()
        for slug in upstream_slugs(upstream):
            print(f"  {slug}{'   [excluded]' if slug in excluded else ''}")
        return 0

    return port(
        args.upstream,
        only=args.only,
        no_render=args.no_render,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())

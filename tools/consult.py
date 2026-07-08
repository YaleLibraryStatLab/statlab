"""
consult.py – recount guides per consultant and post the count to their profile.

Each consultant in data/consultants.json carries a `guides` array of guide
slugs. The app turns those slugs into the clickable authored-guides list on the
profile page, and the team page shows the count as `guides | length` — so the
array drives both the count badge and the linked list.

The authoritative record of authorship is guides_manifest.json, which build.py
writes from each guide's extracted authors. This tool reads the manifest, matches
each guide's author names back to consultants, and overwrites every consultant's
`guides` array so the profiles reflect what the guides actually say.

    python tools/consult.py              # recount and rewrite data/consultants.json
    python tools/consult.py --dry-run    # show the recount; write nothing

Matching is authoritative and overwriting: a consultant's `guides` list is
replaced with exactly the guides the manifest attributes to them (empty if none),
so a stale hand-entered slug is dropped. Author names carry credential suffixes
in the manifest ("Atalay Demiray, MD, MSc"), so names are normalized — comma
suffix stripped, whitespace collapsed, casefolded — before comparison. An author
with no matching consultant profile (e.g. a former consultant) is a warning, not
an error: the run still succeeds so it can slot into the port pipeline.

port_guides.py calls sync() after build.py refreshes the manifest, so a full port
ends with every profile's guide count brought current.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    # `python tools/consult.py` puts tools/ (not the repo root) on sys.path;
    # add the root so `tools.build` resolves the same way it does for app.py.
    sys.path.insert(0, str(ROOT))

from tools.build import DEFAULT_MANIFEST

DEFAULT_CONSULTANTS = ROOT / "data" / "consultants.json"


def _normalize_name(name: str) -> str:
    """Key a name for matching: drop a trailing credential list
    ("Atalay Demiray, MD, MSc" -> "Atalay Demiray"), collapse whitespace,
    casefold. Generalizes the lowercased-name matching app.py already uses."""
    base = name.split(",", 1)[0]
    return " ".join(base.split()).casefold()


def _read_text(path: Path) -> str | None:
    """Return file text, or None (with a warning) if missing/unreadable."""
    if not path.is_file():
        print(f"warning: {path} not found — nothing to recount", file=sys.stderr)
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"warning: could not read {path}: {exc}", file=sys.stderr)
        return None


def _load_json(path: Path):
    """Return parsed JSON, or None (with a warning) if missing/unreadable."""
    raw = _read_text(path)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"warning: could not parse {path}: {exc}", file=sys.stderr)
        return None


# A consultant's inline "guides": [ ... ] value. Guide slugs never contain a
# closing bracket, so [^\]]* safely spans the whole array (empty or not).
_GUIDES_RE = re.compile(r'"guides"\s*:\s*\[[^\]]*\]')


def _rewrite_guides(raw: str, guide_lists: list[list[str]]) -> str | None:
    """Replace each consultant's inline `guides` array in-place, preserving the
    file's hand-formatting everywhere else. Returns None if the number of
    `guides` occurrences doesn't match the consultant count (caller falls back
    to a full reserialize)."""
    if len(_GUIDES_RE.findall(raw)) != len(guide_lists):
        return None
    values = iter(guide_lists)

    def _sub(_match: re.Match) -> str:
        # json.dumps(["a", "b"]) -> '["a", "b"]', json.dumps([]) -> '[]',
        # matching the file's existing inline style.
        return '"guides": ' + json.dumps(next(values), ensure_ascii=False)

    return _GUIDES_RE.sub(_sub, raw)


def sync(
    manifest_path: Path = DEFAULT_MANIFEST,
    consultants_path: Path = DEFAULT_CONSULTANTS,
    *,
    dry_run: bool = False,
) -> int:
    """Recount authored guides per consultant from the manifest and post the
    result to consultants.json. Always returns 0 — an unmatched author or a
    missing file is a warning, not a failure, so this can end a port run."""
    manifest = _load_json(manifest_path)
    raw = _read_text(consultants_path)
    if manifest is None or raw is None:
        return 0
    try:
        consultants = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"warning: could not parse {consultants_path}: {exc}", file=sys.stderr)
        return 0

    # Normalized-name -> consultant. On a name collision the last wins; the
    # consultant list is small and hand-curated, so duplicates are not expected.
    by_name = {_normalize_name(c["name"]): c for c in consultants}

    # id(consultant) -> ordered, de-duplicated slug list. Iterating the manifest
    # in order (build.py emits it slug-sorted) keeps each list deterministic.
    authored: dict[int, list[str]] = {id(c): [] for c in consultants}
    unmatched: list[tuple[str, str]] = []

    for guide in manifest:
        slug = guide["slug"]
        for author in guide.get("authors", []):
            consultant = by_name.get(_normalize_name(author))
            if consultant is None:
                unmatched.append((author, slug))
                continue
            slugs = authored[id(consultant)]
            if slug not in slugs:
                slugs.append(slug)

    guide_lists = [authored[id(c)] for c in consultants]

    changed = False
    print("--- guide recount " + "-" * 42)
    for consultant, new_guides in zip(consultants, guide_lists):
        if consultant.get("guides") != new_guides:
            changed = True
        count = len(new_guides)
        print(f"  {consultant['name']:<28} {count} guide{'' if count == 1 else 's'}")

    if unmatched:
        print(
            "\nwarning: guide authors with no consultant profile "
            "(add a profile or ignore if former):",
            file=sys.stderr,
        )
        for author, slug in unmatched:
            print(f"  {author}  ({slug})", file=sys.stderr)

    if dry_run:
        print("\ndry run: consultants.json not written")
    elif changed:
        # Surgically replace only the `guides` arrays so the file's hand
        # formatting (compact inline topic/tool arrays) is left untouched.
        new_text = _rewrite_guides(raw, guide_lists)
        if new_text is None:
            # Occurrence count didn't line up — fall back to a full reserialize
            # (correct, but reflows every array). Warn so it can be caught.
            print(
                "warning: could not match guides arrays for surgical edit; "
                "reserializing (formatting may change)",
                file=sys.stderr,
            )
            for consultant, new_guides in zip(consultants, guide_lists):
                consultant["guides"] = new_guides
            new_text = json.dumps(consultants, indent=2, ensure_ascii=False) + "\n"
        consultants_path.write_text(new_text, encoding="utf-8")
        print(f"\nwrote {consultants_path.name}")
    else:
        print("\nconsultants.json already current — not rewritten")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recount authored guides per consultant and post to their profile.",
    )
    parser.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST,
        help="guide manifest with author names (default: guides_manifest.json)",
    )
    parser.add_argument(
        "--consultants", type=Path, default=DEFAULT_CONSULTANTS,
        help="consultant data to update (default: data/consultants.json)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the recount; write nothing",
    )
    args = parser.parse_args(argv)
    return sync(args.manifest, args.consultants, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

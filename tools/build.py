"""
build.py – single ingestion command for the research-guide pipeline.

Turns rendered Quarto guides into everything the Flask app needs:

    python tools/build.py              # publish to temp/, write guides_manifest.json
    python tools/build.py --dry-run    # show what would be published, write nothing
    python tools/build.py --clean      # also remove published guides that left the source set

For every directory under the source tree (default research-guides/) that is
not excluded and contains <slug>/<slug>.html, the build:

1. runs extractor.extract() as a smoke check — a parse failure skips the
   guide with a loud warning instead of crashing the build,
2. verifies every local asset referenced by the extracted HTML exists on
   disk (the asset-404 smoke test from ALPHA.md) and reports missing files,
3. copies the guide directory into the publish dir (default temp/), and
4. classifies each guide into stable browse topics, and
5. records slug / title / date / authors / keywords / topics in guides_manifest.json
   at the repo root.

Guide selection is exclusion-based: a finished guide publishes by default,
and guides.exclude (one slug per line, "#" starts a comment) lists the ones
held back. An exclusion that matches no source directory is a warning, not
an error: guides excluded upstream are never ported here, so their entries
legitimately match nothing. The strict typo check runs in port_guides.py
against the upstream catalog (pass --strict-exclusions to error here too).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    # `python tools/build.py` puts tools/ (not the repo root) on sys.path;
    # add the root so `tools.extractor` resolves the same way it does for
    # app.py and pytest.
    sys.path.insert(0, str(ROOT))

from tools.extractor import ExtractedGuide, extract
from tools.guide_topics import (
    DEFAULT_OVERRIDES as DEFAULT_TOPIC_OVERRIDES,
    TopicConfigError,
    classify_manifest,
    load_overrides,
)

DEFAULT_SOURCE = ROOT / "research-guides"
DEFAULT_DEST = ROOT / "temp"
DEFAULT_EXCLUDE_FILE = ROOT / "guides.exclude"
DEFAULT_MANIFEST = ROOT / "guides_manifest.json"

# research-guides/guides/ is the archived pre-Flask listing site, not a guide.
LEGACY_DIRS = {"guides"}

# Per-guide publish contract: every file committed under <guide>/assets/ ships
# verbatim and is downloadable at /guides/<slug>/assets/<path>. port_guides.py
# exempts this directory from its source/cache filters for the same reason.
ASSETS_DIRNAME = "assets"

# Nothing here matches assets/ — the whole tree passes through untouched.
_COPY_IGNORE = shutil.ignore_patterns(".DS_Store", ".quarto")


def load_exclusions(path: Path) -> set[str]:
    """Parse an exclusion file: one slug per line, '#' starts a comment."""
    slugs = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            slugs.add(entry)
    return slugs


def unmatched_exclusions(excluded: set[str], source: Path) -> list[str]:
    return sorted(slug for slug in excluded if not (source / slug).is_dir())


def discover_guide_dirs(source: Path, excluded: set[str]) -> list[Path]:
    """Non-excluded, non-legacy guide directories, sorted by slug."""
    return sorted(
        entry
        for entry in source.iterdir()
        if entry.is_dir()
        and not entry.name.startswith(".")
        and entry.name not in LEGACY_DIRS
        and entry.name not in excluded
    )


def find_missing_assets(guide: ExtractedGuide, guide_dir: Path) -> list[str]:
    """Local paths referenced by the extracted HTML that don't exist on disk.

    Covers <head> stylesheets/scripts, <img> sources, and <a href> targets — the
    last of these catches dead download links, e.g. a guide whose rendered HTML
    predates its data moving into assets/.

    Only paths relative to the guide directory are checked; server-absolute
    paths (e.g. /assets/...) are resolved by Flask routes, not the guide copy.
    """
    missing = []
    seen: set[str] = set()
    for asset in (*guide.stylesheets, *guide.scripts, *guide.images, *guide.links):
        if not asset.is_local:
            continue
        # urlparse drops any #fragment and ?query; unquote turns %20 back into
        # the real filename on disk.
        rel = unquote(urlparse(asset.src).path)
        if not rel or rel.startswith("/") or rel in seen:
            continue
        seen.add(rel)
        if not (guide_dir / rel).exists():
            missing.append(rel)
    return missing


def partition_missing(missing: list[str]) -> tuple[list[str], list[str]]:
    """Split missing targets into absent files and unresolved links.

    A file extension is the discriminator. "assets/data/nunn.csv" is a real
    file that should exist; "@sec-methods" (an unresolved Quarto cross-
    reference) and "TODO-link-ols-guide" (an author placeholder) are prose
    defects. Both are reported, but keeping them apart stops a guide's
    half-written xrefs from burying a genuinely missing dataset.
    """
    files, unresolved = [], []
    for rel in missing:
        (files if PurePosixPath(rel).suffix else unresolved).append(rel)
    return files, unresolved


def inventory_assets(guide_dir: Path) -> list[str]:
    """POSIX paths, relative to the guide dir, of every file under assets/.

    This is the guide's published download set. Paths stay relative: the
    /statlab/ prefix comes from STATLAB_URL_PREFIX at freeze time and must be
    applied by url_for(), never baked into the committed manifest.
    """
    assets_dir = guide_dir / ASSETS_DIRNAME
    if not assets_dir.is_dir():
        return []
    return sorted(
        path.relative_to(guide_dir).as_posix()
        for path in assets_dir.rglob("*")
        if path.is_file() and not path.name.startswith(".")
    )


def copy_guide(src_dir: Path, dest_dir: Path) -> None:
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(src_dir, dest_dir, ignore=_COPY_IGNORE)


def clean_dest(dest: Path, source: Path, excluded: set[str], *, dry_run: bool) -> list[str]:
    """Remove publish-dir guides that are excluded or gone from the source tree.

    A guide that merely failed this run's smoke check is still in the source
    set, so its previous published copy is kept.
    """
    removed = []
    if not dest.is_dir():
        return removed
    for entry in sorted(dest.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name in excluded or not (source / entry.name).is_dir():
            removed.append(entry.name)
            if not dry_run:
                shutil.rmtree(entry)
    return removed


def build(
    source: Path = DEFAULT_SOURCE,
    dest: Path = DEFAULT_DEST,
    exclude_file: Path = DEFAULT_EXCLUDE_FILE,
    manifest_path: Path = DEFAULT_MANIFEST,
    topic_overrides_path: Path = DEFAULT_TOPIC_OVERRIDES,
    *,
    dry_run: bool = False,
    clean: bool = False,
    strict_exclusions: bool = False,
) -> int:
    source = source.resolve()
    dest = dest.resolve()

    if not source.is_dir():
        print(f"error: source directory not found: {source}", file=sys.stderr)
        return 1
    if dest == source:
        print("error: --dest must differ from --source (a build would delete the sources)", file=sys.stderr)
        return 1

    if exclude_file.is_file():
        excluded = load_exclusions(exclude_file)
    elif exclude_file == DEFAULT_EXCLUDE_FILE:
        excluded = set()
        print(f"note: no exclusion file at {exclude_file} — publishing every guide")
    else:
        print(f"error: exclusion file not found: {exclude_file}", file=sys.stderr)
        return 1

    unmatched = unmatched_exclusions(excluded, source)
    if unmatched:
        severity = "error" if strict_exclusions else "warning"
        print(
            f"{severity}: exclusion entries match no directory under {source}:\n"
            + "".join(f"  - {slug}\n" for slug in unmatched)
            + ("Fix the typo or remove the entry (was the guide renamed?)."
               if strict_exclusions
               else "Expected when a guide is excluded upstream before porting; "
                    "port_guides.py checks these against the full catalog."),
            file=sys.stderr,
        )
        if strict_exclusions:
            return 1

    guide_dirs = discover_guide_dirs(source, excluded)
    try:
        topic_overrides = load_overrides(
            topic_overrides_path,
            known_slugs=(guide_dir.name for guide_dir in guide_dirs),
        )
    except TopicConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    manifest = []
    skipped = 0
    missing_total = 0
    unresolved_total = 0
    assets_total = 0

    for guide_dir in guide_dirs:
        slug = guide_dir.name
        html_file = guide_dir / f"{slug}.html"
        if not html_file.is_file():
            print(
                f"WARNING: skipped {slug} — no {slug}.html "
                f"(rename the rendered HTML or add the slug to {exclude_file.name})",
                file=sys.stderr,
            )
            skipped += 1
            continue

        try:
            guide = extract(html_file)
        except Exception as exc:
            print(f"WARNING: skipped {slug} — extractor failed: {exc}", file=sys.stderr)
            skipped += 1
            continue

        missing_files, unresolved = partition_missing(find_missing_assets(guide, guide_dir))
        if missing_files:
            missing_total += len(missing_files)
            print(
                f"WARNING: {slug} references {len(missing_files)} missing file(s) "
                f"— these will 404 (re-render the guide if its data moved):",
                file=sys.stderr,
            )
            for rel in missing_files:
                print(f"    {rel}", file=sys.stderr)
        if unresolved:
            unresolved_total += len(unresolved)
            print(
                f"WARNING: {slug} has {len(unresolved)} unresolved link(s) "
                f"— broken cross-references or TODO placeholders in the source:",
                file=sys.stderr,
            )
            for rel in unresolved:
                print(f"    {rel}", file=sys.stderr)

        assets = inventory_assets(guide_dir)
        assets_total += len(assets)

        if not dry_run:
            copy_guide(guide_dir, dest / slug)

        manifest.append({
            "slug": slug,
            "title": guide.title or slug,
            "date": guide.date,
            "authors": [a.name for a in guide.authors],
            "keywords": guide.keywords,
            "assets": assets,
            # Used only by the classifier and removed before JSON is written.
            "_abstract": guide.abstract,
        })
        detail = f" ({len(assets)} asset{'' if len(assets) == 1 else 's'})" if assets else ""
        print(f"  {'would publish' if dry_run else 'published'}: {slug}{detail}")

    if clean:
        for name in clean_dest(dest, source, excluded, dry_run=dry_run):
            print(f"  {'would remove' if dry_run else 'removed'}: {dest.name}/{name}")

    manifest, unclassified = classify_manifest(manifest, topic_overrides)
    for slug in unclassified:
        print(
            f"WARNING: no browse topic matched {slug}; it will remain visible "
            "under All guides. Add guide keywords or a topic override.",
            file=sys.stderr,
        )

    manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
    if dry_run:
        print(manifest_json)
    else:
        manifest_path.write_text(manifest_json + "\n", encoding="utf-8")
        print(f"wrote {manifest_path.name} ({len(manifest)} guides)")

    print(
        f"{'dry run: ' if dry_run else ''}{len(manifest)} published, "
        f"{skipped} skipped, {assets_total} downloadable asset(s), "
        f"{missing_total} missing file(s), {unresolved_total} unresolved link(s)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Publish rendered research guides for the Flask app.",
    )
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_SOURCE,
        help="directory of rendered guides (default: research-guides/)",
    )
    parser.add_argument(
        "--dest", type=Path, default=DEFAULT_DEST,
        help="publish directory served by the app (default: temp/)",
    )
    parser.add_argument(
        "--exclude-file", type=Path, default=DEFAULT_EXCLUDE_FILE,
        help="exclusion list, one slug per line (default: guides.exclude)",
    )
    parser.add_argument(
        "--topic-overrides", type=Path, default=DEFAULT_TOPIC_OVERRIDES,
        help="per-guide topic corrections (default: data/guide_topic_overrides.json)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print the manifest and planned actions; write nothing",
    )
    parser.add_argument(
        "--clean", action="store_true",
        help="remove publish-dir guides that are excluded or gone from the source tree",
    )
    parser.add_argument(
        "--strict-exclusions", action="store_true",
        help="fail (instead of warn) on exclusion entries matching no source directory",
    )
    args = parser.parse_args(argv)
    return build(
        source=args.source,
        dest=args.dest,
        exclude_file=args.exclude_file,
        topic_overrides_path=args.topic_overrides,
        dry_run=args.dry_run,
        clean=args.clean,
        strict_exclusions=args.strict_exclusions,
    )


if __name__ == "__main__":
    sys.exit(main())

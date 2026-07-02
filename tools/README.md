# tools/

Pipeline utilities for converting Quarto-compiled research guides into
Flask-served content.

---

## Files

| File | Purpose |
|------|---------|
| `extractor.py` | Parse a single Quarto HTML file; extract content, metadata, assets |
| `build.py` | Single ingestion command: walk `research-guides/`, smoke-check each guide with the extractor, verify local assets exist, copy accepted guides to `temp/`, write `guides_manifest.json` |
| `guide_topics.py` | Assign stable browse topics from guide metadata; imported by `build.py`, with preview/check/write commands and optional overrides in `data/guide_topic_overrides.json` |
| `port_guides.py` | Mirror the guide directories committed on the upstream repo's **main** branch into `research-guides/`, reading via git so the upstream working tree / checked-out branch is irrelevant. Pulls main's committed rendered HTML (no `quarto render`), removes local guides no longer on main, then runs `build.py --clean`. `--ref` reads a different ref; `--only <slug>` ports one guide without pruning the rest |

---

## Quick start

```bash
# Mirror main: port every guide on main (minus exclusions) and publish it
python tools/port_guides.py

# Preview what would be ported/removed; change nothing
python tools/port_guides.py --dry-run

# List the guides on main and their exclusion status
python tools/port_guides.py --list

# Port a single guide (e.g. from a feature branch) without re-syncing the rest
python tools/port_guides.py --only logit-probit --ref origin/logit-probit

# Re-publish what's already in research-guides/ to temp/ + manifest
python tools/build.py            # (--clean also drops temp/ guides no longer present)

# Human-readable summary of one guide
python tools/extractor.py research-guides/mixed-effects-models/mixed-effects-models.html

# Full JSON dump (pipe to jq, etc.)
python tools/extractor.py research-guides/olsregression/olsregression.html --json
```

Guide selection is automatic. `port_guides.py` takes every guide directory on
the upstream **main** branch, drops anything listed in `guides.exclude` (the
authoring template), mirrors the rest into `research-guides/`, and removes
local guides that are no longer on main. `build.py` then publishes
`research-guides/` → `temp/`. The only hand-maintained input is
`guides.exclude`; every entry must be a real directory on main or
`port_guides.py` fails loudly. (`build.py` also reads `guides.exclude` and only
warns — not fails — when an entry has no local directory, which is normal: the
template is excluded and never copied locally.)

`extract()` returns an `ExtractedGuide` dataclass with:

```
.title          str
.authors        list[Author]   # name, url, affiliation
.date           str | None     # ISO date from dcterms.date
.abstract       str | None     # inner HTML, label stripped
.keywords       list[str]
.quarto_version str | None
.main_html      str            # cleaned inner HTML of <main>
.scripts        list[Asset]
.stylesheets    list[Asset]
.images         list[Asset]
```

---

## Quarto HTML anatomy

```
<head>
  <!-- inline CSS reset (always present) -->
  <!-- local assets under <guide>_files/libs/
       clipboard, quarto-html, popper, tippy, anchor, bootstrap, mermaid -->
  <!-- CDN: polyfill.io (or cdnjs), MathJax 3 -->
</head>

<body class="fullcontent [quarto-light]">
  <div id="quarto-content">
    <main class="content" id="quarto-document-content">
      <header id="title-block-header" class="quarto-title-block default">
        <!-- title, authors, affiliations, date, abstract, keywords -->
      </header>
      <!-- body sections: level1 h1, level2 h2, ... -->
    </main>
  </div>
  <!-- quarto runtime JS injected after </main> -->
</body>
```

---

## Edge cases and Flask adaptations

### Asset paths
Local assets live in `<guide-name>_files/libs/` relative to the HTML file.
When serving from Flask you must either:

- Copy the `_files/` directory into `static/guides/<slug>/` and rewrite paths,
  **or**
- Serve the `research-guides/` tree directly as a static directory.

`extractor.rewrite_asset_paths()` handles the rewriting once you decide on a
URL prefix.

### Quarto version differences
Bootstrap CSS filenames are hashed in Quarto ≥ 1.7
(`bootstrap-<hash>.min.css`).  The extractor captures the full filename
verbatim, so no special handling is needed — just copy the file as-is.

### MathJax
Both polyfill and MathJax are loaded from CDN.  The CDN URL changed between
Quarto versions (`polyfill.io` → `cdnjs.cloudflare.com`).  Both are captured
in `guide.scripts`.  In production you may want to bundle MathJax locally to
avoid the CDN dependency.

### Callout boxes
`div.callout-note / callout-important / callout-caution / callout-warning / callout-tip`
are styled by Bootstrap + a small slice of Quarto CSS.  The icons render via
Bootstrap Icons (`bi-*`).  Make sure `bootstrap-icons.css` is loaded.

### Tabsets
`.panel-tabset` uses Bootstrap tabs (JS) + `quarto.js` / `tabsets.js`.  Both
are included in the local `_files/libs/quarto-html/` directory.  Load them in
the Flask template **after** Bootstrap JS.

### Collapsible code blocks
`<details class="code-fold">` is native HTML5 — no JS required.

### Mermaid diagrams
`<pre class="mermaid mermaid-js">` blocks need `mermaid.min.js` and
`mermaid-init.js` from `_files/libs/quarto-diagram/`.  They auto-render on
`DOMContentLoaded`.

### Code copy buttons
`.code-copy-button` calls `clipboard.js`.  Include
`_files/libs/clipboard/clipboard.min.js` and add the click handler that
Quarto's `quarto.js` normally registers.  Alternatively, replace the copy
button with a simpler custom implementation in your Flask template.

### Cross-references
`<a href="#fig-X" class="quarto-xref">` are in-page anchors and work as-is
when the full `main_html` is embedded.  Broken `@sec-*` references (unresolved
in the .qmd source) appear as literal `@sec-name` strings in the HTML — flag
these during ingestion if needed.

### Citations & bibliography
`<span class="citation" data-cites="...">` links and the `<div id="refs"
class="references csl-bib-body">` block are plain HTML with no runtime
dependencies.

### Code tools dropdown (removed)
Quarto renders a "Code ▾" dropdown with "Show All Code / Hide All Code / View
Source" options.  **View Source** fetches the `.qmd` file by URL — that file
won't exist in the Flask context.  The extractor removes the entire dropdown
(`button.code-tools-button`) to avoid broken fetch requests.

### Emoji spans
`<span class="emoji" data-emoji="grin">😁</span>` — the text node already
contains the emoji character; no JS or CSS is needed.

### Multi-author guides
Both `<meta name="author">` (one per author) and the rendered
`.quarto-title-meta-author` block are parsed.  The rendered block is preferred
because it includes author URLs and affiliation text.

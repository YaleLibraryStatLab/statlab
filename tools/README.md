# tools/

Pipeline utilities for converting Quarto-compiled research guides into
Flask-served content.

---

## Files

| File | Purpose |
|------|---------|
| `extractor.py` | Parse a single Quarto HTML file; extract content, metadata, assets |
| `build.py` | Single ingestion command: walk `research-guides/`, smoke-check each guide with the extractor, verify local assets exist, copy accepted guides to `temp/`, write `guides_manifest.json` |
| `port_guides.py` | Render guides in the upstream ResearchGuides repo (`quarto render`), copy the output into `research-guides/<slug>/` (normalizing the main HTML to `<slug>.html`), then run `build.py`. `--no-render` skips quarto; `--only <slug>` ports one guide |

---

## Quick start

```bash
# Full pipeline: render every non-excluded upstream guide and publish it
python tools/port_guides.py

# Port one guide whose upstream HTML is already rendered (no quarto run)
python tools/port_guides.py --only standard-errors --no-render

# Re-publish what's already in research-guides/ to temp/ + manifest
python tools/build.py

# Preview without writing anything
python tools/build.py --dry-run

# Also remove temp/ guides that are excluded or gone from research-guides/
python tools/build.py --clean

# Human-readable summary of one guide
python tools/extractor.py research-guides/mixed-effects-models/mixed-effects-models.html

# Full JSON dump (pipe to jq, etc.)
python tools/extractor.py research-guides/standard-errors/standard-errors.html --json
```

Guide selection is exclusion-based: every `research-guides/<slug>/` containing
`<slug>.html` publishes unless the slug is listed in `guides.exclude` at the
repo root (one slug per line, `#` comments). `port_guides.py` validates every
exclusion entry against the upstream catalog, so typos and renamed guides
surface immediately; `build.py` only warns on entries matching no local
directory (expected for guides excluded upstream before porting — pass
`--strict-exclusions` to make it fail instead).

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

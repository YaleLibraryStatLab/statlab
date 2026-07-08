# Beta Test Readiness

Outstanding work before StatLab is ready for beta testing — the beta successor
to `ALPHA.md` / `alpha-test-checklist.md`.

## Source repos

Two repos feed the live site; each item below is tagged with the one(s) it
touches.

- **statlab** (this repo) — the Flask app that ingests rendered guides and
  builds the public site: templates, styling, the guide TOC, the code-language
  switcher, and the freeze → GitHub Pages deploy. Owns *how a guide looks and
  behaves on the site*.
- **research-guides** — the Quarto guide sources (prose, code, diagrams,
  references, recommended readings). Locally `../ResearchGuides`
  (github.com/YaleLibraryStatLab/YUL-StatLab); rendered HTML is ported into
  statlab with `make port`. Owns *what a guide says and runs*.

## Outstanding items

### 1. Mermaid diagrams don't render
Mermaid diagrams do not render visibly in the new (Flask/frozen) guide format.
- **Repo:** statlab

### 2. Code-language coverage + honest signalling
Either extend the code-language coverage of existing guides, or give an honest
indication of which languages we currently support — plus a note on when we
hope to add more.
- **Repo:** research-guides (write the additional-language code) · statlab
  (design the "languages available" display and the "coming soon" note)

### 3. Consultant portfolio auto-updates when they publish a guide
The deploy framework should detect when a consultant has authored a new guide
and add it to their portfolio on the website.
- **Repo:** statlab (deploy/build check + consultant ↔ guide linkage)

### 4. Guide TOC — show level-4 headings
The left-rail table of contents should include level-4 (`<h4>`) headings.
- **Repo:** research-guides

### 5. Recommended readings per guide
Every guide should carry a list of recommended readings — kept INDEPENDENT of
the references — that point readers to good starting positions for their work.
- **Repo:** research-guides

### 6. Separate content-generation code from method-demonstration code
Decide an optimal treatment for code that *generates content* inside a Quarto
document (e.g. simulation data) versus code that *demonstrates a method /
implementation*. Content-generation code should NOT respond to the code
sidebar / language switcher.
- **Repo:** research-guides (tabset / collapse changes) · statlab (switcher UX)

## Open questions
_To be filled in once we agree how to structure and prioritise this list._

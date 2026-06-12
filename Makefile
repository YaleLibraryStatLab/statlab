VENV   := .venv
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest

.PHONY: dev port port-render port-all build test freeze

dev:
	$(PYTHON) app.py

# Quick copy of one already-rendered upstream guide (no quarto run)
port:
	@test -n "$(SLUG)" || { echo "usage: make port SLUG=<slug>"; exit 1; }
	$(PYTHON) tools/port_guides.py --only $(SLUG) --no-render

# Render one guide upstream with quarto, then port it
port-render:
	@test -n "$(SLUG)" || { echo "usage: make port-render SLUG=<slug>"; exit 1; }
	$(PYTHON) tools/port_guides.py --only $(SLUG)

# Full pipeline: render + port every non-excluded upstream guide
port-all:
	$(PYTHON) tools/port_guides.py

build:
	$(PYTHON) tools/build.py

test:
	$(PYTEST)

freeze:
	@echo "make freeze: placeholder — pending D-1 deploy-freeze plan (see ALPHA.md)"

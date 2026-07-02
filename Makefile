VENV   := .venv
PYTHON := $(VENV)/bin/python
PYTEST := $(VENV)/bin/pytest

.PHONY: dev port port-one build test freeze

dev: freeze
	$(PYTHON) app.py

# Mirror every guide on the upstream main branch into research-guides/ + temp/
port:
	$(PYTHON) tools/port_guides.py

# Port a single guide without pruning the rest; SLUG required, REF optional
#   make port-one SLUG=logit-probit
#   make port-one SLUG=logit-probit REF=origin/logit-probit
port-one:
	@test -n "$(SLUG)" || { echo "usage: make port-one SLUG=<slug> [REF=<ref>]"; exit 1; }
	$(PYTHON) tools/port_guides.py --only $(SLUG) $(if $(REF),--ref $(REF),)

build:
	$(PYTHON) tools/build.py --clean

test:
	$(PYTEST)

# Freeze the current temp/ + manifest into a static site under docs/ for
# GitHub Pages (served from the /statlab/ prefix). Run `make build` first to
# refresh temp/ from research-guides/.
freeze:
	$(PYTHON) tools/freeze.py

# YHWH Ya' Way Makefile — common workflows for `make` users.
# All targets dispatch through `./ebible` (the unified CLI).
# For richer subcommands (search, quality flags, etc.), call `./ebible` directly.

.PHONY: help status doctor build build-force ship ship-full audit test repl watch \
        inject manifest quality clean cleanup epubcheck \
        commit-ready ci ci-fast

# Default target — show the available recipes
help:
	@./ebible help

status:
	@./ebible status

doctor:
	@./ebible doctor

# Full pipeline: source notes → master HTML → 5 editions → validation
build:
	@./ebible build

# Convenience: bypass incremental cache and rebuild everything
build-force:
	@./ebible build --force

# ship-check (default mode)
ship:
	@./ebible ship

# Full integrity gate (ship-check + the opt-in epubcheck gate)
ship-full:
	@./ebible ship --epubcheck

# Code-quality CI gate (vulture/mypy/pip-audit/caches — kept off the live dashboard)
audit:
	@./ebible audit

test:
	@./ebible test

repl:
	@./ebible repl

# Auto-rebuild on note edits
watch:
	@./ebible watch

# Pass-through shortcuts
inject:
	@./ebible inject --all-books

manifest:
	@./ebible manifest --build

quality:
	@./ebible quality

epubcheck:
	@./ebible epubcheck

cleanup:
	@./ebible cleanup

# "ready to commit" — runs ship-check + tests, exits non-zero on failure
commit-ready: ship test
	@echo "✓ ship-check + tests passed. Safe to commit."

# W4.5 — local CI gate: ruff format-check · ruff check (report) · lint_rules ·
# mypy (typed surface) · pytest · coverage floor. Composes the blocking gates
# into one command (no git remote yet, so CI runs locally). Exits non-zero if
# any blocking gate fails. The coverage floor activates once `coverage` is
# installed (pip install -r requirements-dev.txt).
ci:
	@python scripts/ci.py

# Fast pre-edit gate: everything except the test suite + coverage.
ci-fast:
	@python scripts/ci.py --no-tests

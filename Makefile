# E-Bible Makefile — common workflows for `make` users.
# All targets dispatch through `./ebible` (the unified CLI).
# For richer subcommands (search, quality flags, etc.), call `./ebible` directly.

.PHONY: help status doctor build build-force ship ship-full test repl watch \
        inject manifest quality clean cleanup epubcheck \
        commit-ready

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

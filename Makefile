# Deep Research Agent Documentation Makefile

.PHONY: docs docs-clean docs-serve help

PYTHON := .venv/bin/python

help:
	@echo "📚 Deep Research Agent Documentation Commands"
	@echo "  docs       - Build API documentation"
	@echo "  docs-clean - Clean and rebuild documentation"  
	@echo "  docs-serve - Build and serve documentation"

docs:
	@echo "🔨 Building documentation..."
	$(PYTHON) build_docs.py

docs-clean:
	@echo "🧹 Cleaning and rebuilding documentation..."
	$(PYTHON) build_docs.py --clean

docs-serve:
	@echo "🌐 Building docs and starting server..."
	$(PYTHON) build_docs.py --serve

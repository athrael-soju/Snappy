#!/bin/bash
# Simple wrapper around cloc to count lines of code
# Excludes common directories like node_modules, .venv, build artifacts, etc.

cloc . --exclude-dir=.venv,venv,env,__pycache__,.mypy_cache,.pytest_cache,.tox,build,dist,node_modules,.next,.git

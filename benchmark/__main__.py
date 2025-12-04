"""
Entry point for running benchmark as a module.

Usage:
    python -m benchmark --help
    python -m benchmark --strategies all --max-samples 100
"""

from .runner import main

if __name__ == "__main__":
    main()

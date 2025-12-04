"""
Allow running benchmarks as a module: python -m benchmarks
"""

from benchmarks.cli import main

if __name__ == "__main__":
    exit(main())

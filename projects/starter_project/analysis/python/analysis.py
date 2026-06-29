#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
FIGURES = ROOT / "figures" / "final"


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    print(f"Project root: {ROOT}")
    print("Replace this template with project-specific Python analysis.")


if __name__ == "__main__":
    main()


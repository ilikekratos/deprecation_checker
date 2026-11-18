"""Run both v1 steps for a folder, against a Python environment:
    1. collector_v1.py    what the folder's notebooks and .py files use   -> methods_present_in_project_v1.json
    2. check_v1.py        look it up in the environment's libraries       -> what might be broken

Usage:  uv run v1/pipeline_v1.py [venv] [folder]     (defaults: .venv and the current folder)
"""
import argparse
import os
from pathlib import Path

import check_v1
import collector_v1
from utils_v1 import use_venv


def main():
    parser = argparse.ArgumentParser(description="Check what a folder uses from libraries against an environment.")
    parser.add_argument("venv", nargs="?", default=".venv", help="the Python environment (default: .venv)")
    parser.add_argument("folder", nargs="?", default=".", help="the notebooks and .py files (default: .)")
    args = parser.parse_args()
    os.environ["VENV"] = args.venv
    use_venv()                                         # from here on, run with the environment's Python
    collector_v1.collect(Path(args.folder))
    check_v1.main()                                    # exit code 1 if something might be broken


if __name__ == "__main__":
    main()

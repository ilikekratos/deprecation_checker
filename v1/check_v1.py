"""
Look up every name in methods_present_in_project_v1.json in .venv (or VENV=path) and list the ones
that might be broken. Exit code 1 if anything might be broken.

Usage:  uv run v1/check_v1.py
"""
import sys
import warnings
from pathlib import Path

import message_v1
from utils_v1 import MISSING, OUTPUT, find, read_json, use_venv


def main():
    venv = use_venv()
    warnings.simplefilter("ignore")                    # libraries warn when they are imported
    if not Path(OUTPUT).exists():
        sys.exit(message_v1.not_collected(OUTPUT))
    missing = missing_names(read_json(OUTPUT))
    print(message_v1.might_be_broken(missing, venv) if missing else message_v1.all_found(venv))
    sys.exit(1 if missing else 0)


def missing_names(used):
    """The names not found in the installed libraries:
        {"pandas": {"pandas": {"DataFrame": ["applymap"]}}}  -> ["pandas.DataFrame.applymap"]"""
    missing = []
    for modules in used.values():
        for module, classes in modules.items():
            path = module.split(".")
            if find(path) is MISSING:
                missing.append(module)
                continue
            for cls, methods in classes.items():
                if find(path + [cls]) is MISSING:
                    missing.append(module + "." + cls)
                    continue
                for method in methods:
                    if find(path + [cls, method]) is MISSING:
                        missing.append(module + "." + cls + "." + method)
    return missing


if __name__ == "__main__":
    main()

"""
Collect what the project uses from libraries, without running it -> methods_present_in_project_v1.json
    {library: {module: {class: [methods]}}}

Only ast, nothing is followed through the code. For each notebook and .py file:
    1. read the imports       import pandas as pd        -> pd means pandas
    2. record every use       pd.DataFrame.merge(a, b)   -> pandas / DataFrame / merge

Usage:  uv run v1/collector_v1.py [folder]
"""
import ast  # Python's own parser: reads code as a tree, without running it
import sys
from pathlib import Path

import message_v1
from utils_v1 import OUTPUT, Reference, custom_names, name_parts, not_libraries, parse, project_files, write_json


def main():
    collect(Path(sys.argv[1] if len(sys.argv) > 1 else "."))


def collect(folder):
    """Write methods_present_in_project_v1.json for the notebooks and .py files in folder."""
    files = project_files(folder)
    skip = not_libraries(files)                        # the project's own modules and the standard library
    used = {}
    for path in files:
        for reference in read_file(path):
            if reference.library not in skip:
                add(used, reference)
    write_json(OUTPUT, used)
    print(message_v1.written(OUTPUT, len(used)))


def read_file(path):
    """The library names one notebook or .py file uses, as References:
        import pandas as pd       ->  Reference("pandas")
        pd.DataFrame.merge(a, b)  ->  Reference("pandas", ("DataFrame", "merge"))"""
    nodes = []
    for tree in parse(path):
        nodes.extend(ast.walk(tree))
    meanings, found = read_imports(nodes)              # 1
    for name in custom_names(nodes):                   # def f(pd) or pd = None: pd may not be the import
        meanings.pop(name, None)
    for node in nodes:                                 # 2
        names = name_parts(node)
        if names and names[0] in meanings:
            meaning = meanings[names[0]]
            found.append(Reference(meaning.module, meaning.path + tuple(names[1:])))
    return found


def read_imports(nodes):
    """What each imported name means, and what the import lines themselves use:
        import matplotlib.pyplot as plt  ->  plt means Reference("matplotlib.pyplot")
        import matplotlib.pyplot         ->  matplotlib means Reference("matplotlib")
        from pandas import merge         ->  merge means Reference("pandas", ("merge",))"""
    meanings, found = {}, []
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.append(Reference(alias.name))
                if alias.asname:
                    meanings[alias.asname] = Reference(alias.name)
                else:
                    root = alias.name.split(".")[0]
                    meanings[root] = Reference(root)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:  # not `from . import x`
            for alias in node.names:
                if alias.name == "*":                  # from x import *: only the module is known
                    found.append(Reference(node.module))
                else:
                    reference = Reference(node.module, (alias.name,))
                    found.append(reference)
                    meanings[alias.asname or alias.name] = reference
    return meanings, found


def add(used, reference):
    """Record one use into used = {library: {module: {class: {methods}}}}. In a long path the last two
    names are the class and method:
        Reference("pandas", ("DataFrame", "merge"))        -> pandas / DataFrame / merge
        Reference("pandas", ("DataFrame", "plot", "bar"))  -> pandas.DataFrame / plot / bar"""
    module, path = reference
    if len(path) > 2:
        module, path = module + "." + ".".join(path[:-2]), path[-2:]
    if reference.library not in used:
        used[reference.library] = {}
    if module not in used[reference.library]:
        used[reference.library][module] = {}
    names = used[reference.library][module]
    if path and path[0] not in names:
        names[path[0]] = set()
    if len(path) > 1:
        names[path[0]].add(path[1])


if __name__ == "__main__":
    main()

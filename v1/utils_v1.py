"""Shared helpers for the _v1 scripts."""
import ast  # Python's own parser: reads code as a tree, without running it
import importlib
import inspect
import json
import os
import sys
import sysconfig
from pathlib import Path
from typing import NamedTuple

import message_v1

OUTPUT = "methods_present_in_project_v1.json"   # {library: {module: {class: [methods]}}}
MISSING = object()


class Reference(NamedTuple):
    """What a name refers to:  pd -> Reference("pandas"),  merge -> Reference("pandas", ("merge",))"""
    module: str
    path: tuple = ()

    @property
    def library(self):
        """The top-level package:  Reference("sqlalchemy.orm").library -> "sqlalchemy" """
        return self.module.split(".")[0]


def project_files(root):
    """Every notebook and .py file under root, except hidden folders (.venv, .git, ...) and v1/."""
    tools = Path(__file__).resolve().parent
    files = []
    for path in sorted(root.rglob("*")):
        hidden = any(part.startswith(".") for part in path.relative_to(root).parts)
        if path.suffix in (".ipynb", ".py") and not hidden and tools not in path.resolve().parents:
            files.append(path)
    return files


def stdlib():
    """Names of the standard-library modules:  {"os", "json", "re", ...}"""
    if hasattr(sys, "stdlib_module_names"):  # Python 3.10+
        return set(sys.stdlib_module_names)
    folder = Path(sysconfig.get_paths()["stdlib"])  # older Pythons: list the standard-library folder
    return {p.name.split(".")[0] for p in list(folder.iterdir()) + list((folder / "lib-dynload").glob("*"))}


def not_libraries(files):
    """The project's own module names and the standard library:  mylib/helper.py -> "mylib", "helper", "os", ..."""
    own = set()
    for path in files:
        if path.suffix == ".py":
            own.add(path.stem)
            own.add(path.parent.name)
    return own | stdlib() | set(sys.builtin_module_names)


def parse(path):
    """The ast of every code cell (a .py file is one cell). % and ! lines are blanked, broken cells skipped."""
    if path.suffix == ".py":
        cells = [path.read_text(encoding="utf-8")]
    else:
        cells = []
        for cell in json.loads(path.read_text(encoding="utf-8")).get("cells", []):
            if cell.get("cell_type") == "code":
                cells.append("".join(cell.get("source", "")))
    trees = []
    for code in cells:
        lines = []
        for line in code.splitlines():
            is_magic = line.lstrip().startswith(("%", "!"))   # %matplotlib inline, !pip install ...
            lines.append("" if is_magic else line)
        try:
            trees.append(ast.parse("\n".join(lines)))
        except SyntaxError:
            pass
    return trees


# Reading Python code

def name_parts(node):
    """pd.DataFrame.merge -> ["pd", "DataFrame", "merge"],  pd -> ["pd"],  pd.read_csv("a").head -> []"""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.insert(0, node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        return [node.id] + parts
    return []


def custom_names(nodes):
    """Names the code gives its own value:  pd = None,  def f(pd),  for pd in ...  ->  {"pd"}"""
    names = set()
    for node in nodes:
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


# The JSON file

def write_json(name, data):
    text = json.dumps(data, indent=2, sort_keys=True, default=sorted)  # default=sorted: sets -> lists
    Path(name).write_text(text + "\n", encoding="utf-8")


def read_json(name):
    return json.loads(Path(name).read_text(encoding="utf-8"))


# The installed libraries

def use_venv():
    """Re-run the script with the Python of VENV (default .venv) unless it already runs there. Returns VENV."""
    venv = Path(os.environ.get("VENV", ".venv")).resolve()
    if Path(sys.prefix).resolve() != venv:
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not python.exists():
            sys.exit(message_v1.no_environment(venv))
        os.execv(str(python), [str(python)] + sys.argv)
    return venv


def find(names):
    """What names[0].names[1]... is in the installed libraries, or MISSING. Imports submodules when
    needed (PIL.Image):  ["pandas", "DataFrame"]  -> <class pandas.DataFrame>"""
    try:
        obj = importlib.import_module(names[0])
        for name in names[1:]:
            if inspect.ismodule(obj) and not hasattr(obj, name):
                importlib.import_module(obj.__name__ + "." + name)
            obj = getattr(obj, name)
        return obj
    except Exception:
        return MISSING

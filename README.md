# Library simple version (v1)

Checks that the library names the notebooks and `.py` files use still exist in the installed
libraries. The code is parsed, with `ast`.

The `.venv` is produced from `pyproject.toml`

Run from the repo root, both steps at once:

```bash
uv run v1/pipeline_v1.py [venv] [folder]
```

Such a script can be run at build phase of an image

## Some misses that come to mind:

- methods on what a call returns: `df = pd.read_csv("a")`, then `df.groupby("x")`, checks only `pd.read_csv`
- names given a library value, or passed to a function: `y = pd.DataFrame`, then `y.merge`
- an imported name the file also assigns (`def f(pd)`, `pd = None`)
- a name imported twice (`import a as x`, then `from b import x`)
- names given as strings: `getattr(pd, "x")`
- `from x import *`: only `x` itself is checked

## Some fixes, just ideas

- remember that `df` holds what `pd.read_csv` returns. Then, in the check
  step, ask the installed library what `read_csv` gives back (a
  DataFrame) and look for `groupby` there. When a library doesn't tell, could mark as unknown.
- follow the names through the code: after
  `y = pd.DataFrame`, treat `y` like `pd.DataFrame`, and repeat until there is nothing new.

## Files

| File | Does |
|---|---|
| `pipeline_v1.py` | both steps, for a venv and a folder |
| `collector_v1.py` | step 1: the imports, and every name that starts with one |
| `check_v1.py` | step 2: looks the names up |
| `utils_v1.py`, `message_v1.py` | shared helpers, and the text the scripts print |
| `test_v1.py` | the tests: `uv run v1/test_v1.py` |
| `collector_v1.mmd` | a diagram of the flow |

## Found

- `plotly.express.scatter_mapbox`: not in plotly 7.1
- when local also epo library related stuff appears as they are not installed

## Alternative to inspect
- also searched and played around with pyright library(https://github.com/microsoft/pyright), and came out with same result :"scatter_mapbox" is not a known attribute of module "plotly.express"


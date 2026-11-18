def where(venv):
    return "the installed libraries (%s)" % venv


def listed(names):
    return "\n".join("  " + name for name in names)


def no_environment(venv):
    return "No Python environment at %s (set VENV=path)" % venv


def not_collected(name):
    return "%s not found: run  uv run v1/collector_v1.py  first" % name


def written(name, libraries):
    return "wrote %s (%d libraries)" % (name, libraries)


def all_found(venv):
    return "All names used in the project were found in %s." % where(venv)


def might_be_broken(names, venv):
    return "WARNING: %d name(s) used in the project might be broken, they could not be found in %s:\n%s" % (
        len(names), where(venv), listed(names))

"""Command registry. Register every command here, once."""

from . import auth, config, project
from .meta import SPECS as META_SPECS
from .whoami import SPEC as WHOAMI

SPECS = []
for module in (auth, config, project):
    SPECS.extend(module.SPECS)
SPECS.append(WHOAMI)
SPECS.extend(META_SPECS)


def all_specs():
    return {tuple(spec["path"]): spec for spec in SPECS}

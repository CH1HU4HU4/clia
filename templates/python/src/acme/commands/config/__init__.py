"""Config commands, registered once."""

from .get import SPEC as GET
from .list import SPEC as LIST
from .set import SPEC as SET
from .unset import SPEC as UNSET

GROUP = {
    "path": ("config",),
    "summary": "Read and write CLI configuration",
    "description": "Inspect and update the user config. Project config never holds secrets.",
    "group": True,
}

SPECS = [GROUP, GET, SET, LIST, UNSET]

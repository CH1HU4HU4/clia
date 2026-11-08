"""Project commands, registered once."""

from .delete import SPEC as DELETE
from .get import SPEC as GET
from .list import SPEC as LIST
from .create import SPEC as CREATE
from .update import SPEC as UPDATE

GROUP = {
    "path": ("project",),
    "summary": "Work with projects",
    "description": "Create, inspect, update, and delete projects.",
    "group": True,
}

SPECS = [GROUP, LIST, GET, CREATE, UPDATE, DELETE]

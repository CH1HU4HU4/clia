"""Meta commands."""

from .completion import SPEC as COMPLETION
from .help_cmd import SPEC as HELP
from .schema import SPEC as SCHEMA
from .version import SPEC as VERSION

SPECS = [VERSION, COMPLETION, SCHEMA, HELP]

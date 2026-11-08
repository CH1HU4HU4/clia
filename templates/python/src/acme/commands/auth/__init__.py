"""Auth commands, registered once."""

from .login import SPEC as LOGIN
from .logout import SPEC as LOGOUT
from .status import SPEC as STATUS

GROUP = {
    "path": ("auth",),
    "summary": "Authenticate and inspect credentials",
    "description": "Log in, log out, and check the current credential.",
    "group": True,
}

SPECS = [GROUP, LOGIN, LOGOUT, STATUS]

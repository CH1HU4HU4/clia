#!/usr/bin/env python3
"""The pre-existing, human-only CLI for the "extend" eval. Intentionally rough."""

import json
import os
import sys
from urllib.request import Request, urlopen


def main(argv):
    base = "https://api.acme.com"
    if "--base-url" in argv:
        index = argv.index("--base-url")
        base = argv[index + 1]
        del argv[index:index + 2]
    token = os.environ.get("ACME_TOKEN") or input("API token: ")
    if argv[:2] == ["project", "list"]:
        request = Request(base.rstrip("/") + "/v1/projects",
                          headers={"authorization": "Bearer " + token})
        with urlopen(request, timeout=10) as response:
            page = json.loads(response.read().decode())
        print("ID        NAME      STATUS")
        for project in page.get("data", [])[:10]:
            print("%-9s %-9s %s" % (project["id"], project["name"], project["status"]))
        return 0
    print("usage: old_cli.py project list", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

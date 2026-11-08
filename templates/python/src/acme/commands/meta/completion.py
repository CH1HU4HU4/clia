"""Print shell completions. Never touches the network."""

from __future__ import annotations

from ...constants import TOOL
from ...errors import UsageError
from ...output import print_text

SPEC = {
    "path": ("completion",),
    "summary": "Generate shell completions",
    "description": "Print a completion script for bash, zsh, or fish.",
    "arguments": [{"name": "shell", "description": "bash, zsh, or fish", "required": True}],
    "flags": [],
    "examples": ["acme completion bash", "acme completion zsh > ~/.zsh/completions/_acme"],
    "data": False,
}


def _words():
    from .. import all_specs
    paths = sorted(" ".join(path) for path in all_specs() if not all_specs()[path].get("group"))
    return paths


def _flags():
    from ...args import GLOBAL_FLAGS
    names = [item["long"] for item in GLOBAL_FLAGS]
    from .. import all_specs
    for spec in all_specs().values():
        names.extend(item["long"] for item in spec.get("flags", []))
    return sorted(set(names))


def run(ctx, opts, positionals):
    shell = positionals[0]
    words = _words()
    flags = _flags()
    if shell == "bash":
        print_text(
            "_%s_completions() {\n"
            "  local cur=\"${COMP_WORDS[COMP_CWORD]}\"\n"
            "  local words=\"%s\"\n"
            "  local flags=\"%s\"\n"
            "  COMPREPLY=( $(compgen -W \"$words $flags\" -- \"$cur\") )\n"
            "}\n"
            "complete -F _%s_completions %s" % (TOOL, " ".join(words), " ".join(flags), TOOL, TOOL)
        )
    elif shell == "zsh":
        print_text(
            "#compdef %s\n"
            "_%s() {\n"
            "  local -a words\n"
            "  words=(%s)\n"
            "  _describe 'command' words\n"
            "}\n"
            "_%s" % (TOOL, TOOL, " ".join(words), TOOL)
        )
    elif shell == "fish":
        lines = ["# fish completions for %s" % TOOL]
        for word in words:
            parts = word.split(" ")
            if len(parts) == 1:
                lines.append("complete -c %s -f -a %s" % (TOOL, parts[0]))
            else:
                lines.append("complete -c %s -f -n '__fish_seen_subcommand_from %s' -a %s"
                             % (TOOL, parts[0], parts[1]))
        print_text("\n".join(lines))
    else:
        raise UsageError("unknown shell %r" % shell, "Use bash, zsh, or fish")
    return 0

SPEC["run"] = run

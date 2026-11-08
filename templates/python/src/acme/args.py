"""Flag parsing, command matching, and usage errors.

One parser for every command. Command specs declare their own flags; global
flags come from GLOBAL_FLAGS. Both `--flag value` and `--flag=value` work.
"""

from __future__ import annotations

from .errors import UsageError

TRUE_WORDS = ("1", "true", "yes", "on")
FALSE_WORDS = ("0", "false", "no", "off")


def flag(long, kind="bool", desc="", metavar=None, default=None, env=None, short=None, repeat=False):
    return {
        "long": long,
        "kind": kind,
        "desc": desc,
        "metavar": metavar,
        "default": default,
        "env": env,
        "short": short,
        "repeat": repeat,
    }


GLOBAL_FLAGS = [
    flag("--json", desc="Print one JSON document on stdout"),
    flag("--quiet", desc="Print identifiers only"),
    flag("--no-color", desc="Disable ANSI color (also NO_COLOR)"),
    flag("--no-input", desc="Fail instead of prompting"),
    flag("--yes", desc="Confirm destructive actions without a prompt"),
    flag("--dry-run", desc="Print the request and send nothing"),
    flag("--debug", desc="Verbose logs to stderr, redacted"),
    flag("--timeout", "value", "Request timeout in seconds", "<seconds>", "30", "ACME_TIMEOUT"),
    flag("--profile", "value", "Config profile", "<name>", None, "ACME_PROFILE"),
    flag("--org", "value", "Override the org for this command", "<id>", None, "ACME_ORG"),
    flag("--project", "value", "Override the project for this command", "<id>", None, "ACME_PROJECT"),
    flag("--api-version", "value", "Override the pinned API version", "<version>", None, "ACME_API_VERSION"),
    flag("--base-url", "value", "Override the API base URL", "<url>", None, "ACME_BASE_URL"),
    flag("--allow-http", desc="Allow plain http for a non-loopback host"),
    flag("--token", "value", "API token (prefer ACME_TOKEN)", "<token>", None, "ACME_TOKEN"),
    flag("--help", desc="Show help", short="-h"),
    flag("--version", desc="Print the version (root command only)"),
]


def key(name):
    return name.lstrip("-").replace("-", "_")


def index_flags(specs):
    by_long = {}
    by_short = {}
    for spec in [None] + list(specs.values()):
        flags = GLOBAL_FLAGS if spec is None else list(GLOBAL_FLAGS) + list(spec.get("flags", []))
        for item in flags:
            by_long.setdefault(item["long"], item)
            if item.get("short"):
                by_short.setdefault(item["short"], item)
    return by_long, by_short


def _take_value(argv, index, name, inline):
    if inline is not None:
        return inline, index
    if index + 1 >= len(argv):
        raise UsageError("Flag %s needs a value" % name, "Pass %s <value>" % name)
    return argv[index + 1], index + 1


def tokenize(argv, by_long, by_short):
    """Split argv into flag occurrences and bare words, respecting flag arity."""
    occurrences = []
    words = []
    index = 0
    after_dashdash = False
    while index < len(argv):
        token = argv[index]
        if after_dashdash:
            words.append(token)
            index += 1
            continue
        if token == "--":
            after_dashdash = True
            index += 1
            continue
        if token.startswith("--"):
            name, equals, inline = token.partition("=")
            definition = by_long.get(name)
            if definition is None and name.startswith("--no-"):
                base = "--" + name[5:]
                base_def = by_long.get(base)
                if base_def is not None and base_def["kind"] == "bool":
                    occurrences.append((base_def, base, False))
                    index += 1
                    continue
            if definition is None:
                guess = suggest(name, sorted(by_long))
                hint = 'did you mean "%s"?' % guess if guess else None
                raise UsageError('unknown flag "%s"' % name, hint)
            if definition["kind"] == "value":
                value, index = _take_value(argv, index, name, inline if equals else None)
                occurrences.append((definition, name, value))
            else:
                value = True
                if equals:
                    lowered = inline.strip().lower()
                    if lowered in TRUE_WORDS:
                        value = True
                    elif lowered in FALSE_WORDS:
                        value = False
                    else:
                        raise UsageError("Flag %s takes true or false, got %r" % (name, inline))
                occurrences.append((definition, name, value))
            index += 1
            continue
        if token.startswith("-") and token != "-":
            definition = by_short.get(token)
            if definition is None:
                raise UsageError('unknown flag "%s"' % token, 'Run acme --help for global flags')
            if definition["kind"] == "value":
                value, index = _take_value(argv, index, token, None)
                occurrences.append((definition, definition["long"], value))
            else:
                occurrences.append((definition, definition["long"], True))
            index += 1
            continue
        words.append(token)
        index += 1
    return occurrences, words


def levenshtein(left, right):
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for i, lchar in enumerate(left, 1):
        current = [i]
        for j, rchar in enumerate(right, 1):
            cost = 0 if lchar == rchar else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]


def suggest(word, candidates):
    best = None
    best_distance = 99
    for candidate in candidates:
        distance = levenshtein(word, candidate)
        if distance < best_distance:
            best = candidate
            best_distance = distance
    if best is not None and best_distance <= max(2, len(word) // 3 + 1):
        return best
    return None


def match_command(words, specs):
    if not words:
        return None, 0
    if len(words) >= 2 and tuple(words[:2]) in specs:
        return specs[tuple(words[:2])], 2
    if tuple(words[:1]) in specs:
        return specs[tuple(words[:1])], 1
    top = [path[0] for path in specs if len(path) == 1]
    hint = None
    guess = suggest(words[0], top)
    if guess:
        hint = 'did you mean "%s"?' % guess
    raise UsageError('unknown command "%s"' % " ".join(words[:2]), hint)


def parse(argv, specs):
    by_long, by_short = index_flags(specs)
    occurrences, words = tokenize(argv, by_long, by_short)
    spec, consumed = match_command(words, specs)

    positionals = words[consumed:]
    if spec is not None and spec.get("group"):
        if positionals:
            children = [path[-1] for path in specs if path[:-1] == spec["path"]]
            guess = suggest(positionals[0], children)
            hint = 'did you mean "%s %s"?' % (spec["path"][0], guess) if guess else None
            raise UsageError('unknown command "%s"' % " ".join(spec["path"] + tuple(positionals[:1])), hint)

    allowed = list(GLOBAL_FLAGS) + (list(spec.get("flags", [])) if spec else [])
    allowed_longs = set(item["long"] for item in allowed)
    opts = {}
    for item in allowed:
        if item.get("repeat") and item.get("default") is None:
            opts[key(item["long"])] = []
        else:
            opts[key(item["long"])] = item.get("default")
    for definition, name, value in occurrences:
        if definition is None or (name not in allowed_longs and definition["long"] not in allowed_longs):
            candidates = sorted(allowed_longs)
            guess = suggest(name, candidates)
            hint = 'did you mean "%s"?' % guess if guess else None
            raise UsageError('unknown flag "%s"' % name, hint)
        if definition.get("repeat"):
            opts[key(definition["long"])].append(value)
        else:
            opts[key(definition["long"])] = value

    if opts.get("help"):
        return spec, opts, positionals

    if spec is not None:
        arguments = spec.get("arguments", [])
        required = sum(1 for argument in arguments if argument.get("required"))
        if len(positionals) > len(arguments):
            raise UsageError(
                "unexpected argument %r" % positionals[len(arguments)],
                "Usage: %s %s %s" % ("acme", " ".join(spec["path"]), _usage_tail(spec)),
            )
        if len(positionals) < required:
            missing = arguments[len(positionals)]["name"]
            raise UsageError("missing required argument <%s>" % missing,
                             "Usage: %s %s %s" % ("acme", " ".join(spec["path"]), _usage_tail(spec)))
    return spec, opts, positionals


def _usage_tail(spec):
    parts = []
    for argument in spec.get("arguments", []):
        parts.append("<%s>" % argument["name"] if argument.get("required") else "[%s]" % argument["name"])
    parts.append("[flags]")
    return " ".join(parts)

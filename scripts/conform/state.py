"""Checker state: one place for running commands and recording verdicts."""

from __future__ import annotations

import os

from .discover import META
from .util import Runner


class Ctx:
    def __init__(self, runner, cfg, report, repo, cli_doc, xdg, home, mock,
                 base_url, token):
        self.runner = runner
        self.cfg = cfg
        self.report = report
        self.repo = repo
        self.cli_doc = cli_doc
        self.xdg = xdg
        self.home = home
        self.mock = mock
        self.base_url = base_url
        self.token = token
        self.commands = {}
        self.tool = cfg.get("tool") or "cli"
        self.token_env = cfg["token_env"]

    # -- running ----------------------------------------------------------
    def run(self, args, stdin=b"", env_extra=None, timeout=None, cwd=None):
        return self.runner.run(args, stdin=stdin, env_extra=env_extra,
                               timeout=timeout, cwd=cwd)

    def run_cmd(self, command, extra=None, **kwargs):
        return self.run(list(command["path"]) + list(extra or []), **kwargs)

    def offline(self, args, timeout=8):
        env = {
            self.token_env: None,
            "NO_COLOR": None,
            "XDG_CONFIG_HOME": os.path.join(self.xdg, "offline"),
        }
        for name in ("BASE_URL", "PROFILE", "OUTPUT", "API_VERSION", "ORG"):
            env[self.token_env.rsplit("_", 1)[0] + "_" + name] = None
        return self.run(args, env_extra=env, timeout=timeout)

    # -- verdicts ---------------------------------------------------------
    def check(self, rule_id, ok, detail=""):
        self.report.add(rule_id, "PASS" if ok else "FAIL", detail)
        return bool(ok)

    def na(self, rule_id, reason):
        self.report.add(rule_id, "N/A", reason)
        return True

    def defer(self, rule_id, reason):
        self.report.add(rule_id, "DEFERRED", reason)
        return True

    def review(self, rule_id, detail=""):
        self.report.add(rule_id, "REVIEW", detail)
        return True

    def skip(self, rule_id, reason):
        self.report.add(rule_id, "SKIP", reason)

    # -- commands ---------------------------------------------------------
    def command(self, *path):
        return self.commands.get(tuple(path))

    def data_commands(self):
        return [command for path, command in sorted(self.commands.items())
                if command.get("data", True) and path[0] not in META
                and not command.get("group")]

    def verbs(self):
        out = {}
        for command in self.commands.values():
            if command.get("group") or len(command["path"]) < 2:
                continue
            verb = command["path"][-1]
            out.setdefault(verb, []).append(command)
        return out

    def resource_command(self, verb):
        path = (self.cfg["resource"], verb)
        return self.commands.get(path)

    def has_flag(self, command, name):
        return any(flag.get("name") == name for flag in command.get("flags", []))

    def config_file(self):
        template = self.cfg.get("config_path") or "{xdg}/{tool}/config.toml"
        return template.replace("{xdg}", self.xdg).replace("{tool}", self.tool)

    def example_commands(self, command):
        """Examples that are safe and shell-free enough to execute."""
        out = []
        for example in command.get("examples") or []:
            if any(char in example for char in ">|&;$`"):
                continue
            out.append(example)
        return out

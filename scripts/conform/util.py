"""Process runner, mock control, and small helpers for the checker."""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import time
from urllib.request import Request, urlopen

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[+-][0-9A-Za-z.+-]+)?$")
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


class Result:
    def __init__(self, args, code, out, err, ms):
        self.args = args
        self.code = code
        self.out = out
        self.err = err
        self.ms = ms

    @property
    def stdout(self):
        return self.out

    @property
    def stderr(self):
        return self.err

    def json_out(self):
        try:
            return json.loads(self.out)
        except ValueError:
            return None

    def json_err(self):
        try:
            return json.loads(self.err)
        except ValueError:
            return None

    def __repr__(self):
        return "<Result %s exit=%s>" % (" ".join(self.args), self.code)


class Runner:
    def __init__(self, binary, cwd, env, timeout=25):
        self.binary = shlex.split(binary) if isinstance(binary, str) else list(binary)
        self.cwd = cwd
        self.env = env
        self.timeout = timeout

    def run(self, args=None, stdin=b"", env_extra=None, timeout=None, cwd=None):
        argv = list(self.binary) + list(args or [])
        env = dict(self.env)
        if env_extra:
            for key, value in env_extra.items():
                if value is None:
                    env.pop(key, None)
                else:
                    env[key] = str(value)
        if stdin is None:
            stdin = b""
        started = time.perf_counter()
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd or self.cwd,
                env=env,
                input=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout or self.timeout,
            )
            code, out, err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as err:
            code = -9
            out = err.stdout or b""
            err = (err.stderr or b"") + b"\n[checker] command timed out\n"
        except FileNotFoundError as err:
            code = -2
            out = b""
            err = str(err).encode()
        return Result(argv, code, out.decode("utf-8", "replace"),
                      err.decode("utf-8", "replace"), int((time.perf_counter() - started) * 1000))

    def run_path(self, path, args=None, **kwargs):
        return self.run(list(path) + list(args or []), **kwargs)


def http_json(url, method="GET", timeout=5):
    data = b"" if method == "POST" else None
    request = Request(url, data=data, method=method)
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class Mock:
    """A running mock API, or a client for --base-url."""

    def __init__(self, script=None, repo=None):
        self.script = script
        self.repo = repo
        self.process = None
        self.base_url = None

    def start(self, extra_args=None):
        if self.script is None:
            raise RuntimeError("no mock script")
        self.process = subprocess.Popen(
            [sys.executable, self.script, "--port", "0", "--quiet", "--host", "0.0.0.0"]
            + list(extra_args or []),
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("mock server did not start")
        port = json.loads(line)["port"]
        self.base_url = "http://127.0.0.1:%d" % port
        return self.base_url

    def attach(self, base_url):
        self.base_url = base_url
        return self.base_url

    def stop(self):
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def call(self, path, method="GET"):
        return http_json(self.base_url + path, method=method)

    def stats(self):
        return self.call("/__debug/stats")

    def reset(self):
        return self.call("/__debug/reset", method="POST")

    def revoke_refresh(self):
        return self.call("/__debug/revoke_refresh", method="POST")

    def seed_short_token(self):
        return self.call("/__debug/seed_and_expire", method="POST")


def walk_keys(payload, prefix=""):
    """Yield every object key in a JSON payload."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield key
            for nested in walk_keys(value):
                yield nested
    elif isinstance(payload, list):
        for item in payload:
            for nested in walk_keys(item):
                yield nested


def walk_scalars(payload):
    if isinstance(payload, dict):
        for value in payload.values():
            for item in walk_scalars(value):
                yield item
    elif isinstance(payload, list):
        for value in payload:
            for item in walk_scalars(value):
                yield item
    else:
        yield payload


def key_case_ok(key, convention):
    if convention == "camel":
        return bool(re.match(r"^[a-z][A-Za-z0-9]*$", key))
    if convention == "kebab":
        return bool(re.match(r"^[a-z][a-z0-9-]*$", key))
    return bool(re.match(r"^[a-z][a-z0-9_]*$", key))


def has_ansi(text):
    return bool(ANSI.search(text or ""))


def describe(result):
    return "exit %s; stdout %r; stderr %r" % (
        result.code,
        (result.out or "")[:160],
        (result.err or "")[:160],
    )


def run_tty(argv, cwd, env, expect=b"Continue?", answer=b"n\n", timeout=10):
    """Run under a pseudo-terminal, answer one prompt, and return (code, text)."""
    import pty
    import select

    master, slave = pty.openpty()
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdin=slave,
                            stdout=slave, stderr=slave, close_fds=True)
    os.close(slave)
    buffer = b""
    sent = False
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            ready, _, _ = select.select([master], [], [], 0.2)
            if ready:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                buffer += chunk
                if not sent and expect in buffer:
                    os.write(master, answer)
                    sent = True
            if proc.poll() is not None and not ready:
                break
        if proc.poll() is None:
            proc.kill()
        code = proc.wait(timeout=5)
    finally:
        try:
            os.close(master)
        except OSError:
            pass
    return code, buffer.decode("utf-8", "replace"), sent


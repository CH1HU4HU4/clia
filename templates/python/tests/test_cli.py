"""Unit and integration tests. Run: python3 -m unittest discover -s tests -v"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from acme.args import GLOBAL_FLAGS, parse, suggest  # noqa: E402
from acme.commands import all_specs  # noqa: E402
from acme.errors import CliError, UsageError, code_for_status, error_payload  # noqa: E402
from acme.help import command_help, have_specs, root_help  # noqa: E402
from acme.output import list_envelope, render_table  # noqa: E402
from acme.redact import mask, redact_headers  # noqa: E402

SPECS = all_specs()


class ArgsTest(unittest.TestCase):
    def test_equals_and_repeat(self):
        _spec, opts, positionals = parse(
            ["project", "list", "--limit=5", "--filter", "status=active", "--filter", "owner=me"],
            SPECS,
        )
        self.assertEqual(opts["limit"], "5")
        self.assertEqual(opts["filter"], ["status=active", "owner=me"])
        self.assertEqual(positionals, [])

    def test_boolean_false_forms(self):
        _spec, opts, _ = parse(["project", "delete", "prj_1", "--yes=false"], SPECS)
        self.assertFalse(opts["yes"])
        _spec, opts, _ = parse(["project", "list", "--all"], SPECS)
        self.assertTrue(opts["all"])

    def test_unknown_flag_suggests(self):
        with self.assertRaises(UsageError) as caught:
            parse(["project", "list", "--limt", "5"], SPECS)
        self.assertIn("--limit", caught.exception.hint)

    def test_unknown_command_suggests(self):
        with self.assertRaises(UsageError) as caught:
            parse(["projet", "list"], SPECS)
        self.assertIn("project", caught.exception.hint)

    def test_missing_positional(self):
        with self.assertRaises(UsageError):
            parse(["project", "get"], SPECS)

    def test_double_dash(self):
        _spec, _opts, positionals = parse(["project", "get", "--", "--weird"], SPECS)
        self.assertEqual(positionals, ["--weird"])

    def test_suggest(self):
        self.assertEqual(suggest("projet", ["project", "config"]), "project")


class OutputTest(unittest.TestCase):
    def test_table_keeps_columns(self):
        text = render_table([("id", "id", None), ("name", "name", 5)],
                            [{"id": "prj_123", "name": "a-very-long-name"}])
        self.assertIn("prj_123", text)
        self.assertIn("ID", text)

    def test_envelope_shape(self):
        envelope = list_envelope([{"id": "a"}], True, "cur_1", False)
        self.assertEqual(set(envelope), {"data", "has_more", "next_cursor", "truncated"})
        self.assertIsInstance(envelope["data"], list)


class RedactTest(unittest.TestCase):
    def test_short_token_is_hidden(self):
        self.assertEqual(mask("test-token"), "****")
        rendered = mask("acme_live_1234567890abcdef")
        self.assertNotIn("1234567890", rendered)

    def test_headers_redacted(self):
        headers = redact_headers({"authorization": "Bearer secret-value", "content-type": "application/json"})
        self.assertNotIn("secret-value", json.dumps(headers))
        self.assertEqual(headers["content-type"], "application/json")


class ErrorMapTest(unittest.TestCase):
    def test_status_map(self):
        self.assertEqual(code_for_status(401), "auth_required")
        self.assertEqual(code_for_status(404), "not_found")
        self.assertEqual(code_for_status(429), "rate_limited")
        self.assertEqual(code_for_status(503), "server_error")

    def test_exit_codes(self):
        self.assertEqual(CliError("not_found", "x").exit, 5)
        self.assertEqual(CliError("confirmation_required", "x").exit, 10)
        self.assertEqual(CliError("ambiguous_target", "x").exit, 11)

    def test_envelope(self):
        payload = error_payload(CliError("not_found", "gone", "hint"), None)
        self.assertEqual(payload["error"]["code"], "not_found")
        self.assertIn("hint", payload["error"])


class HelpTest(unittest.TestCase):
    def setUp(self):
        have_specs(SPECS)

    def test_root_help_has_examples(self):
        text = root_help(SPECS)
        self.assertIn("Examples:", text)
        self.assertIn("acme project list", text)
        self.assertLess(len(text.splitlines()), 60)

    def test_every_command_help_has_two_examples(self):
        for path, spec in SPECS.items():
            if spec.get("group"):
                continue
            text = command_help(spec)
            examples = spec.get("examples") or []
            self.assertGreaterEqual(len(examples), 2, path)
            for example in examples:
                self.assertNotIn("<your", example, path)
            self.assertIn("Flags:", text, path)

    def test_flags_have_long_forms(self):
        for item in GLOBAL_FLAGS:
            self.assertTrue(item["long"].startswith("--"))


class MockHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        pass

    def _send(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.send_header("x-request-id", "req_test")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/v1/projects/prj_001"):
            self._send(200, {"id": "prj_001", "name": "web", "status": "active",
                             "owner": "a@b.c", "description": "d", "created_at": "2026-01-01T00:00:00Z",
                             "updated_at": "2026-01-01T00:00:00Z", "settings": {}, "counts": {},
                             "metadata": {}})
        elif self.path.startswith("/v1/projects/missing"):
            self._send(404, {"error": {"code": "not_found", "message": "Project missing not found",
                                       "hint": "Run acme project list"}})
        elif self.path.startswith("/v1/projects"):
            items = [] if "name=" in self.path else [
                {"id": "prj_001", "name": "web", "status": "active",
                 "owner": "a@b.c", "created_at": "2026-01-01T00:00:00Z",
                 "updated_at": "2026-01-01T00:00:00Z"}]
            self._send(200, {"data": items,
                             "has_more": False, "next_cursor": None})
        elif self.path.startswith("/v1/me"):
            self._send(200, {"user": {"id": "u1", "email": "a@b.c"}, "org": "acme",
                             "environment": "test", "token_expires_at": None})
        else:
            self._send(404, {"error": {"code": "not_found", "message": "no"}})


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), MockHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = dict(os.environ)
        self.env.update({
            "XDG_CONFIG_HOME": self.temp.name,
            "ACME_TOKEN": "test-token",
            "PYTHONPATH": SRC,
        })
        for key in ("ACME_BASE_URL", "ACME_PROFILE", "ACME_OUTPUT"):
            self.env.pop(key, None)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, stdin=None):
        command = [sys.executable, "-m", "acme"] + list(args)
        return subprocess.run(command, env=self.env, input=stdin, capture_output=True,
                              text=True, timeout=20)

    def base(self, *args):
        return self.run_cli(*(list(args) + ["--base-url", "http://127.0.0.1:%d" % self.port]))

    def test_json_list(self):
        result = self.base("project", "list", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["data"][0]["id"], "prj_001")
        self.assertIn("has_more", payload)

    def test_not_found_exit_and_envelope(self):
        result = self.base("project", "get", "missing", "--json")
        self.assertEqual(result.returncode, 5)
        payload = json.loads(result.stderr)
        self.assertEqual(payload["error"]["code"], "not_found")
        self.assertIn("hint", payload["error"])

    def test_delete_without_yes_is_safe(self):
        result = self.base("project", "delete", "prj_001")
        self.assertEqual(result.returncode, 10)
        self.assertIn("--yes", result.stderr)

    def test_help_offline(self):
        env = dict(self.env)
        env.pop("ACME_TOKEN", None)
        result = subprocess.run([sys.executable, "-m", "acme", "project", "list", "--help"],
                                env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Examples:", result.stdout)

    def test_version_is_semver_only(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertRegex(result.stdout.strip(), r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()

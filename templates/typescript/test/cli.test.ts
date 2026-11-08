import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import * as fs from "node:fs";
import { createServer, type Server } from "node:http";
import * as os from "node:os";
import * as path from "node:path";
import { after, before, describe, it } from "node:test";

import { GLOBAL_FLAGS, parse, suggest } from "../src/args.ts";
import { allSpecs } from "../src/commands/index.ts";
import { codeForStatus, CliError, UsageError, errorPayload } from "../src/errors.ts";
import { commandHelp, haveSpecs, rootHelp } from "../src/help.ts";
import { listEnvelope, renderTable } from "../src/output.ts";
import { mask, redactHeaders } from "../src/redact.ts";

const ROOT = path.resolve(import.meta.dirname, "..");
const SPECS = allSpecs();
haveSpecs(SPECS);

describe("args", () => {
  it("accepts --flag=value and repeatable flags", () => {
    const { opts } = parse(["project", "list", "--limit=5", "--filter", "status=active",
      "--filter", "owner=me"], SPECS);
    assert.equal(opts.limit, "5");
    assert.deepEqual(opts.filter, ["status=active", "owner=me"]);
  });

  it("accepts boolean false forms", () => {
    const { opts } = parse(["project", "delete", "prj_1", "--yes=false"], SPECS);
    assert.equal(opts.yes, false);
  });

  it("suggests unknown flags and commands", () => {
    assert.throws(() => parse(["project", "list", "--limt", "5"], SPECS), (err: any) => {
      assert.ok(err instanceof UsageError);
      assert.match(err.hint, /--limit/);
      return true;
    });
    assert.throws(() => parse(["projet", "list"], SPECS), (err: any) => {
      assert.match(err.hint, /project/);
      return true;
    });
  });

  it("requires positionals", () => {
    assert.throws(() => parse(["project", "get"], SPECS), UsageError);
  });

  it("suggests the nearest name", () => {
    assert.equal(suggest("projet", ["project", "config"]), "project");
  });
});

describe("output", () => {
  it("renders a table and keeps IDs", () => {
    const text = renderTable([["id", "id", null], ["name", "name", 5]],
      [{ id: "prj_123", name: "a-very-long-name" }]);
    assert.match(text, /prj_123/);
    assert.match(text, /ID/);
  });

  it("always emits the list envelope", () => {
    const envelope = listEnvelope([{ id: "a" }], true, "cur_1", false);
    assert.deepEqual(Object.keys(envelope), ["data", "has_more", "next_cursor", "truncated"]);
  });
});

describe("redaction and errors", () => {
  it("hides short and long tokens", () => {
    assert.equal(mask("test-token"), "****");
    assert.doesNotMatch(String(mask("acme_live_1234567890abcdef")), /1234567890/);
  });

  it("redacts authorization headers", () => {
    const headers = redactHeaders({ authorization: "Bearer secret-value", "content-type": "application/json" });
    assert.doesNotMatch(JSON.stringify(headers), /secret-value/);
  });

  it("maps statuses to exit codes", () => {
    assert.equal(codeForStatus(401), "auth_required");
    assert.equal(codeForStatus(404), "not_found");
    assert.equal(codeForStatus(503), "server_error");
    assert.equal(new CliError("not_found", "x").exit, 5);
    assert.equal(new CliError("confirmation_required", "x").exit, 10);
    assert.equal(new CliError("ambiguous_target", "x").exit, 11);
  });

  it("builds an error envelope", () => {
    const payload = errorPayload(new CliError("not_found", "gone", "hint"));
    assert.equal((payload as any).error.code, "not_found");
    assert.ok((payload as any).error.hint);
  });
});

describe("help", () => {
  it("keeps root help under 60 lines with examples", () => {
    const text = rootHelp();
    assert.match(text, /Examples:/);
    assert.ok(text.split("\n").length < 60);
  });

  it("gives every command two examples and flags", () => {
    for (const [pathKey, spec] of Object.entries(SPECS)) {
      if (spec.group) continue;
      assert.ok((spec.examples || []).length >= 2, pathKey);
      assert.match(commandHelp(spec), /Flags:/);
    }
  });

  it("only uses long global flags", () => {
    for (const item of GLOBAL_FLAGS) assert.ok(item.long.startsWith("--"));
  });
});

function makeServer(): { server: Server; port: number } {
  const server = createServer((request, response) => {
    const send = (status: number, payload: unknown) => {
      const body = JSON.stringify(payload);
      response.writeHead(status, { "content-type": "application/json", "x-request-id": "req_test" });
      response.end(body);
    };
    const url = new URL(request.url || "/", "http://127.0.0.1");
    if (url.pathname === "/v1/me") {
      send(200, { user: { id: "u1", email: "a@b.c" }, org: "acme", environment: "test" });
    } else if (url.pathname === "/v1/projects/prj_001") {
      send(200, {
        id: "prj_001", name: "web", status: "active", owner: "a@b.c",
        description: "d", created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z", settings: {}, counts: {}, metadata: {},
      });
    } else if (url.pathname.startsWith("/v1/projects/missing")) {
      send(404, { error: { code: "not_found", message: "Project missing not found", hint: "Run acme project list" } });
    } else if (url.pathname === "/v1/projects") {
      const items = url.searchParams.get("name") ? [] : [{
        id: "prj_001", name: "web", status: "active", owner: "a@b.c",
        created_at: "2026-01-01T00:00:00Z", updated_at: "2026-01-01T00:00:00Z",
      }];
      send(200, { data: items, has_more: false, next_cursor: null });
    } else {
      send(404, { error: { code: "not_found", message: "no" } });
    }
  });
  return { server, port: 0 };
}

describe("integration", () => {
  let server: Server;
  let port = 0;
  let temp = "";

  before(async () => {
    const made = makeServer();
    server = made.server;
    await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
    port = (server.address() as any).port;
  });

  after(() => {
    server.close();
    if (temp) fs.rmSync(temp, { recursive: true, force: true });
  });

  function run(args: string[], extraEnv: Record<string, string> = {}): Promise<any> {
    temp = temp || fs.mkdtempSync(path.join(os.tmpdir(), "acme-ts-test-"));
    const env: Record<string, string> = {
      ...process.env as Record<string, string>,
      XDG_CONFIG_HOME: temp,
      ACME_TOKEN: "test-token",
      NO_COLOR: "1",
      ...extraEnv,
    };
    for (const key of ["ACME_BASE_URL", "ACME_PROFILE", "ACME_OUTPUT"]) delete env[key];
    return new Promise((resolve) => {
      const child = spawn(process.execPath, ["bin/acme.ts", ...args], {
        cwd: ROOT, env, stdio: ["ignore", "pipe", "pipe"],
      });
      let stdout = "";
      let stderr = "";
      child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
      child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
      const timer = setTimeout(() => child.kill("SIGKILL"), 20000);
      child.on("close", (code) => {
        clearTimeout(timer);
        resolve({ status: code, stdout, stderr });
      });
    });
  }

  const base = (args: string[]) => run([...args, "--base-url", `http://127.0.0.1:${port}`]);

  it("lists JSON", async () => {
    const result = await base(["project", "list", "--json"]);
    assert.equal(result.status, 0, result.stderr);
    const payload = JSON.parse(result.stdout);
    assert.equal(payload.data[0].id, "prj_001");
    assert.ok("has_more" in payload);
  });

  it("maps not found to exit 5 with an envelope", async () => {
    const result = await base(["project", "get", "missing", "--json"]);
    assert.equal(result.status, 5);
    const payload = JSON.parse(result.stderr);
    assert.equal(payload.error.code, "not_found");
    assert.ok(payload.error.hint);
  });

  it("refuses delete without --yes", async () => {
    const result = await base(["project", "delete", "prj_001"]);
    assert.equal(result.status, 10);
    assert.match(result.stderr, /--yes/);
  });

  it("works offline for help", async () => {
    const result = await run(["project", "list", "--help"]);
    assert.equal(result.status, 0);
    assert.match(result.stdout, /Examples:/);
  });

  it("prints semver only", async () => {
    const result = await run(["--version"]);
    assert.match(result.stdout.trim(), /^\d+\.\d+\.\d+$/);
  });
});

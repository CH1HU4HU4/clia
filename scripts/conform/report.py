"""Human and JSON reports for the conformance checker."""

from __future__ import annotations

import json
import sys

from .rules import RULES

STATUSES = ["PASS", "FAIL", "N/A", "DEFERRED", "REVIEW", "SKIP"]


class Report:
    def __init__(self, name, binary):
        self.name = name
        self.binary = binary
        self.results = {}

    def add(self, rule_id, status, detail=""):
        if status not in STATUSES:
            raise ValueError("bad status " + status)
        self.results[rule_id] = {"status": status, "detail": detail}

    def status(self, rule_id):
        return self.results.get(rule_id, {}).get("status")

    def failed(self, priority=None):
        out = []
        for rule in RULES:
            rule_id, _group, rule_priority, mode, _title = rule
            result = self.results.get(rule_id)
            if not result:
                continue
            if result["status"] != "FAIL":
                continue
            if priority and rule_priority != priority:
                continue
            if mode != "check":
                continue
            out.append(rule_id)
        return out

    def summary(self, priority):
        counts = {status: 0 for status in STATUSES}
        for rule in RULES:
            rule_id, _group, rule_priority, _mode, _title = rule
            if rule_priority != priority:
                continue
            result = self.results.get(rule_id)
            if not result:
                continue
            counts[result["status"]] += 1
        return counts

    def gate(self, strict=False):
        p0_fail = self.failed("P0")
        p1_fail = self.failed("P1")
        ok = not p0_fail and (not strict or not p1_fail)
        return ok, p0_fail, p1_fail

    def text(self, verbose=False, strict=False):
        lines = ["CLIA conformance: %s (%s)" % (self.name, self.binary), ""]
        for rule in RULES:
            rule_id, group, priority, mode, title = rule
            result = self.results.get(rule_id)
            if not result:
                continue
            status = result["status"]
            line = "%-8s %s [%s/%s] %s" % (status, rule_id, priority, mode, title)
            detail = result.get("detail") or ""
            if detail and (verbose or status in ("FAIL", "N/A", "DEFERRED")):
                line += " \u2014 " + detail
            lines.append(line)
        lines.append("")
        for priority in ("P0", "P1"):
            counts = self.summary(priority)
            lines.append("%s: %d pass, %d fail, %d N/A, %d deferred, %d review, %d skip" % (
                priority, counts["PASS"], counts["FAIL"], counts["N/A"],
                counts["DEFERRED"], counts["REVIEW"], counts["SKIP"]))
        ok, p0_fail, p1_fail = self.gate(strict=strict)
        if p0_fail:
            lines.append("P0 failures: " + ", ".join(p0_fail))
        if p1_fail:
            lines.append("P1 failures: " + ", ".join(p1_fail))
        lines.append("Gate: " + ("PASS" if ok else "FAIL"))
        return "\n".join(lines)

    def payload(self, strict=False):
        ok, p0_fail, p1_fail = self.gate(strict=strict)
        rows = []
        for rule in RULES:
            rule_id, group, priority, mode, title = rule
            result = self.results.get(rule_id)
            if not result:
                continue
            rows.append({
                "id": rule_id,
                "group": group,
                "priority": priority,
                "mode": mode,
                "title": title,
                "status": result["status"],
                "detail": result.get("detail", ""),
            })
        return {
            "name": self.name,
            "binary": self.binary,
            "gate": {"pass": ok, "p0_failures": p0_fail, "p1_failures": p1_fail},
            "summary": {"p0": self.summary("P0"), "p1": self.summary("P1")},
            "results": rows,
        }

    def dump_json(self, path):
        with open(path, "w", encoding="utf-8") as stream:
            json.dump(self.payload(), stream, indent=2)

    def print_text(self, verbose=False, strict=False):
        sys.stdout.write(self.text(verbose=verbose, strict=strict) + "\n")


def emit_json(report, path=None, strict=False):
    payload = report.payload(strict=strict)
    text = json.dumps(payload, indent=2)
    if path:
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")

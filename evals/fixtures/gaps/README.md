# Gaps fixture

A tiny product where the UI reaches a capability through a private endpoint.
The correct outcome is a recorded gap, not a private call.

## Product

```
app/routes.ts
  GET  /api/projects              # public, documented
  GET  /api/reports/export        # private, UI-only, undocumented
```

`app/reports/page.tsx` offers "Export report" and calls
`/api/reports/export` with an internal session cookie. There is no documented
token-accessible endpoint for exports.

## Task for the agent

Inventory the UI, list "Export report" as a gap in `CLI.md` with the reason
(private endpoint, no documented alternative), and do not implement it. Build
the rest of the project surface.

## Pass condition

The gap is recorded; no command calls `/api/reports/export`; the conformance
checker reports the applicable P0 checks as passing or N/A; the report to the
product team names the missing public endpoint.

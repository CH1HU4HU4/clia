package cli

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func testContext(serverURL string) *Context {
	return &Context{
		Profile: "default", BaseURL: serverURL, APIVersion: "2026-01-01",
		Output: "json", Token: "test-token", Timeout: 5, Config: defaultConfig(),
	}
}

func TestParseFlagForms(t *testing.T) {
	specs := AllSpecs()
	_, opts, _, err := Parse([]string{"project", "list", "--limit=5", "--filter", "a=b", "--filter", "c=d"}, specs)
	if err != nil {
		t.Fatal(err)
	}
	if opts["limit"] != "5" {
		t.Fatalf("limit = %v", opts["limit"])
	}
	filters := stringSlice(opts, "filter")
	if len(filters) != 2 || filters[0] != "a=b" {
		t.Fatalf("filters = %v", filters)
	}
}

func TestParseUnknownSuggests(t *testing.T) {
	_, _, _, err := Parse([]string{"project", "list", "--limt", "5"}, AllSpecs())
	cliErr, ok := err.(*CLIError)
	if !ok || cliErr.Exit != 2 || !strings.Contains(cliErr.Hint, "--limit") {
		t.Fatalf("unexpected error: %#v", err)
	}
	_, _, _, err = Parse([]string{"projet", "list"}, AllSpecs())
	if cliErr, ok := err.(*CLIError); !ok || !strings.Contains(cliErr.Hint, "project") {
		t.Fatalf("unexpected command error: %#v", err)
	}
}

func TestHelpHasExamplesAndFlags(t *testing.T) {
	specs := AllSpecs()
	root := RootHelp(specs)
	if !strings.Contains(root, "Examples:") || len(strings.Split(root, "\n")) >= 60 {
		t.Fatalf("root help is wrong")
	}
	for key, spec := range specs {
		if spec.Group {
			continue
		}
		if len(spec.Examples) < 2 {
			t.Fatalf("%s has %d examples", key, len(spec.Examples))
		}
		if !strings.Contains(CommandHelp(spec, specs), "Flags:") {
			t.Fatalf("%s help lacks flags", key)
		}
	}
}

func TestMaskAndRedact(t *testing.T) {
	if Mask("test-token") != "****" {
		t.Fatalf("short token not hidden")
	}
	if strings.Contains(Mask("acme_live_1234567890abcdef"), "1234567890") {
		t.Fatalf("long token leaked")
	}
	headers := RedactHeaders(map[string]string{"authorization": "Bearer secret-value"})
	body, _ := json.Marshal(headers)
	if strings.Contains(string(body), "secret-value") {
		t.Fatalf("header leaked")
	}
}

func TestErrorMapping(t *testing.T) {
	cases := map[int]string{401: "auth_required", 404: "not_found", 409: "conflict", 429: "rate_limited", 503: "server_error"}
	for status, code := range cases {
		if got := codeForStatus(status); got != code {
			t.Fatalf("status %d = %s", status, got)
		}
	}
	if newError("not_found", "x", "").Exit != 5 {
		t.Fatalf("not_found exit")
	}
}

func TestListAndGetAgainstServer(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.Header().Set("content-type", "application/json")
		writer.Header().Set("x-request-id", "req_test")
		switch {
		case request.URL.Path == "/v1/projects":
			json.NewEncoder(writer).Encode(map[string]any{
				"data": []any{map[string]any{"id": "prj_001", "name": "web", "status": "active",
					"owner": "a@b.c", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}},
				"has_more": false, "next_cursor": nil,
			})
		case request.URL.Path == "/v1/projects/prj_001":
			json.NewEncoder(writer).Encode(map[string]any{
				"id": "prj_001", "name": "web", "status": "active", "description": "d",
				"created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
				"settings": map[string]any{}, "counts": map[string]any{}, "metadata": map[string]any{},
			})
		default:
			writer.WriteHeader(404)
			json.NewEncoder(writer).Encode(map[string]any{"error": map[string]any{
				"code": "not_found", "message": "Project missing not found", "hint": "Run acme project list"}})
		}
	}))
	defer server.Close()
	ctx := testContext(server.URL)
	api := NewApi(ctx)
	page, err := api.Get("/v1/projects", nil)
	if err != nil {
		t.Fatal(err)
	}
	items := asList(page["data"])
	if len(items) != 1 || items[0].(map[string]any)["id"] != "prj_001" {
		t.Fatalf("page = %v", page)
	}
	if _, err := resolveProject(api, "prj_001"); err != nil {
		t.Fatal(err)
	}
	_, err = api.Get("/v1/projects/missing", nil)
	cliErr, ok := err.(*CLIError)
	if !ok || cliErr.Code != "not_found" || cliErr.Exit != 5 || cliErr.Hint == "" {
		t.Fatalf("unexpected 404 error: %#v", err)
	}
}

func TestNonTTYDeleteRefuses(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
		writer.Header().Set("content-type", "application/json")
		json.NewEncoder(writer).Encode(map[string]any{"id": "prj_001", "name": "web", "status": "active"})
	}))
	defer server.Close()
	ctx := testContext(server.URL)
	ctx.Output = "table"
	_, err := projectDeleteRun(ctx, map[string]any{"yes": false, "dry_run": false}, []string{"prj_001"})
	cliErr, ok := err.(*CLIError)
	if !ok || cliErr.Code != "confirmation_required" || cliErr.Exit != 10 {
		t.Fatalf("delete did not refuse: %#v", err)
	}
	if !strings.Contains(cliErr.Hint, "--yes") {
		t.Fatalf("missing --yes hint")
	}
}

func TestConfigRoundTrip(t *testing.T) {
	temp := t.TempDir()
	old, had := os.LookupEnv("XDG_CONFIG_HOME")
	os.Setenv("XDG_CONFIG_HOME", temp)
	defer func() {
		if had {
			os.Setenv("XDG_CONFIG_HOME", old)
		} else {
			os.Unsetenv("XDG_CONFIG_HOME")
		}
	}()
	if err := SaveConfig(defaultConfig()); err != nil {
		t.Fatal(err)
	}
	info, err := os.Stat(filepath.Join(temp, Tool, "config.toml"))
	if err != nil {
		t.Fatal(err)
	}
	if info.Mode().Perm()&0o077 != 0 {
		t.Fatalf("config mode = %o", info.Mode().Perm())
	}
	if err := setConfigValue("default", "org", "acme", false); err != nil {
		t.Fatal(err)
	}
	data, err := LoadConfig()
	if err != nil {
		t.Fatal(err)
	}
	if data.Profiles["default"]["org"] != "acme" {
		t.Fatalf("org not saved")
	}
}

func TestEnvelopeShape(t *testing.T) {
	envelope := ListEnvelope([]map[string]any{{"id": "a"}}, true, "cur_1", false)
	if len(envelope) != 4 || envelope["has_more"] != true {
		t.Fatalf("envelope = %v", envelope)
	}
}

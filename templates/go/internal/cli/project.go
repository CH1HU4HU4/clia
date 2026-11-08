package cli

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"
	"unicode"
)

var summaryFields = []string{"id", "name", "status", "owner", "created_at", "updated_at"}
var fullFields = append(append([]string{}, summaryFields...), "description", "settings", "counts", "metadata")

var listColumns = []Column{
	{Header: "id", Key: "id"},
	{Header: "name", Key: "name", Cap: 30},
	{Header: "status", Key: "status", Cap: 10},
	{Header: "owner", Key: "owner", Cap: 28},
	{Header: "updated", Key: "updated_at", Cap: 20},
}

var getFields = [][2]string{
	{"id", "id"}, {"name", "name"}, {"status", "status"}, {"owner", "owner"},
	{"description", "description"}, {"created_at", "created_at"},
	{"updated_at", "updated_at"}, {"settings", "settings"}, {"counts", "counts"},
}

func projectPath(projectID string) string {
	return "/v1/projects/" + projectID
}

func resolveProject(api *Api, value string) (map[string]any, error) {
	project, err := api.Get(projectPath(value), nil)
	if err == nil {
		return project, nil
	}
	cliErr, ok := err.(*CLIError)
	if !ok || cliErr.Code != "not_found" {
		return nil, err
	}
	page, err := api.Get("/v1/projects", Query{{"name", value}, {"limit", "2"}})
	if err != nil {
		return nil, err
	}
	matches := asList(page["data"])
	if len(matches) == 1 {
		return api.Get(projectPath(toString(matches[0].(map[string]any)["id"])), nil)
	}
	if len(matches) > 1 {
		candidates := []any{}
		for _, item := range matches {
			project := item.(map[string]any)
			candidates = append(candidates, map[string]any{"id": project["id"], "name": project["name"]})
		}
		first := matches[0].(map[string]any)["id"]
		err := newError("ambiguous_target", fmt.Sprintf("Multiple projects match %q", value),
			fmt.Sprintf("Retry with a project ID, for example: acme project get %v", first))
		err.Extra = map[string]any{"candidates": candidates}
		return nil, err
	}
	return nil, newError("not_found", "Project "+value+" not found", "Run acme project list")
}

func pageLimit(opts map[string]any) (int, error) {
	limit, err := intValue(first(str(opts, "limit"), "50"))
	if err != nil {
		return 0, UsageErr("--limit must be an integer", fmt.Sprintf("Pass a number from 1 to %d", MaxPageSize))
	}
	if limit < 1 || limit > MaxPageSize {
		return 0, UsageErr(fmt.Sprintf("--limit must be between 1 and %d", MaxPageSize),
			fmt.Sprintf("Default is %d", DefaultPageSize))
	}
	return limit, nil
}

func listQuery(opts map[string]any, cursor string) (Query, error) {
	limit, err := pageLimit(opts)
	if err != nil {
		return nil, err
	}
	query := Query{{"limit", fmt.Sprint(limit)}}
	if cursor == "" {
		cursor = str(opts, "cursor")
	}
	if cursor != "" {
		query = append(query, [2]string{"cursor", cursor})
	}
	if sortValue := str(opts, "sort"); sortValue != "" {
		query = append(query, [2]string{"sort", sortValue})
	}
	for _, item := range stringSlice(opts, "filter") {
		query = append(query, [2]string{"filter", item})
	}
	for _, name := range []string{"search", "status", "owner", "since", "until"} {
		if value := str(opts, name); value != "" {
			query = append(query, [2]string{name, value})
		}
	}
	if boolean(opts, "full") {
		query = append(query, [2]string{"full", "1"})
	}
	return query, nil
}

func requestedFields(opts map[string]any) ([]string, error) {
	raw := str(opts, "fields")
	if raw == "" {
		return nil, nil
	}
	allowed := summaryFields
	if boolean(opts, "full") {
		allowed = fullFields
	}
	fields := []string{}
	for _, part := range strings.Split(raw, ",") {
		text := strings.TrimSpace(part)
		if text != "" {
			fields = append(fields, text)
		}
	}
	for _, field := range fields {
		found := false
		for _, candidate := range allowed {
			if field == candidate {
				found = true
				break
			}
		}
		if !found {
			return nil, UsageErr(fmt.Sprintf("unknown field %q", field), "Allowed now: "+strings.Join(allowed, ", "))
		}
	}
	return fields, nil
}

func shape(item map[string]any, full bool, fields []string) map[string]any {
	source := map[string]any{}
	if full {
		for key, value := range item {
			source[key] = value
		}
	} else {
		for _, key := range summaryFields {
			if value, ok := item[key]; ok {
				source[key] = value
			}
		}
	}
	if fields != nil {
		picked := map[string]any{}
		for _, field := range fields {
			picked[field] = source[field]
		}
		return picked
	}
	return source
}

func fetchAll(api *Api, opts map[string]any) ([]map[string]any, bool, string, bool, error) {
	items := []map[string]any{}
	cursor := str(opts, "cursor")
	hasMore := false
	truncated := false
	for {
		query, err := listQuery(opts, cursor)
		if err != nil {
			return nil, false, "", false, err
		}
		page, err := api.Get("/v1/projects", query)
		if err != nil {
			return nil, false, "", false, err
		}
		batch := asList(page["data"])
		for _, raw := range batch {
			if len(items) >= AllCap {
				break
			}
			if project, ok := raw.(map[string]any); ok {
				items = append(items, project)
			}
		}
		hasMore, _ = page["has_more"].(bool)
		cursor = toString(page["next_cursor"])
		if len(items) >= AllCap && (hasMore || boolean(opts, "all")) {
			truncated = true
			break
		}
		if !boolean(opts, "all") || !hasMore || cursor == "" {
			break
		}
	}
	return items, hasMore, cursor, truncated, nil
}

func asList(value any) []any {
	if list, ok := value.([]any); ok {
		return list
	}
	return []any{}
}

func bodyFlags(opts map[string]any) (map[string]any, error) {
	body := map[string]any{}
	if raw := str(opts, "data"); raw != "" {
		var parsed map[string]any
		if err := json.Unmarshal([]byte(raw), &parsed); err != nil {
			return nil, UsageErr("--data is not valid JSON: "+err.Error(), "Pass a JSON object")
		}
		body = parsed
	}
	if path := str(opts, "file"); path != "" {
		if str(opts, "data") != "" {
			warn("--file wins over --data")
		}
		var raw []byte
		var err error
		if path == "-" {
			raw, err = io.ReadAll(os.Stdin)
		} else {
			raw, err = os.ReadFile(path)
		}
		if err != nil {
			return nil, UsageErr("cannot read --file "+path+": "+err.Error(), "")
		}
		var parsed map[string]any
		if err := json.Unmarshal(raw, &parsed); err != nil {
			return nil, UsageErr("--file is not valid JSON: "+err.Error(), "")
		}
		body = parsed
	}
	return body, nil
}

func coerceValue(value string) any {
	switch value {
	case "true":
		return true
	case "false":
		return false
	case "null":
		return nil
	}
	var integer int
	if _, err := fmt.Sscanf(value, "%d", &integer); err == nil && fmt.Sprint(integer) == value {
		return integer
	}
	return value
}

func nestedSet(target map[string]any, dotted string, value any) {
	parts := strings.Split(dotted, ".")
	cursor := target
	for _, part := range parts[:len(parts)-1] {
		next, ok := cursor[part].(map[string]any)
		if !ok {
			next = map[string]any{}
			cursor[part] = next
		}
		cursor = next
	}
	cursor[parts[len(parts)-1]] = value
}

func patchFromFlags(opts map[string]any) (map[string]any, error) {
	patch, err := bodyFlags(opts)
	if err != nil {
		return nil, err
	}
	for _, item := range stringSlice(opts, "set") {
		equals := strings.Index(item, "=")
		if equals < 0 {
			return nil, UsageErr(fmt.Sprintf("--set expects key=value, got %q", item), "Example: --set status=active")
		}
		nestedSet(patch, strings.TrimSpace(item[:equals]), coerceValue(item[equals+1:]))
	}
	for _, item := range stringSlice(opts, "unset") {
		nestedSet(patch, strings.TrimSpace(item), nil)
	}
	return patch, nil
}

func newUUID() string {
	buffer := make([]byte, 16)
	_, _ = rand.Read(buffer)
	return fmt.Sprintf("%s-%s-%s-%s-%s",
		hex.EncodeToString(buffer[0:4]), hex.EncodeToString(buffer[4:6]),
		hex.EncodeToString(buffer[6:8]), hex.EncodeToString(buffer[8:10]),
		hex.EncodeToString(buffer[10:16]))
}

func projectListRun(ctx *Context, opts map[string]any, _ []string) (int, error) {
	api := NewApi(ctx)
	query, err := listQuery(opts, "")
	if err != nil {
		return 0, err
	}
	if boolean(opts, "dry_run") {
		EmitDryRun(api.Preview("GET", "/v1/projects", query, nil, ""), ctx, opts)
		return 0, nil
	}
	fields, err := requestedFields(opts)
	if err != nil {
		return 0, err
	}
	items, hasMore, nextCursor, truncated, err := fetchAll(api, opts)
	if err != nil {
		return 0, err
	}
	shaped := []map[string]any{}
	for _, item := range items {
		shaped = append(shaped, shape(item, boolean(opts, "full"), fields))
	}
	EmitList(shaped, ctx, opts, listColumns, "projects", hasMore, nextCursor, truncated)
	return 0, nil
}

func projectGetRun(ctx *Context, opts map[string]any, positionals []string) (int, error) {
	api := NewApi(ctx)
	if boolean(opts, "dry_run") {
		EmitDryRun(api.Preview("GET", projectPath(positionals[0]), nil, nil, ""), ctx, opts)
		return 0, nil
	}
	fields, err := requestedFields(opts)
	if err != nil {
		return 0, err
	}
	project, err := resolveProject(api, positionals[0])
	if err != nil {
		return 0, err
	}
	EmitObject(shape(project, true, fields), ctx, opts, getFields)
	return 0, nil
}

func projectCreateRun(ctx *Context, opts map[string]any, _ []string) (int, error) {
	api := NewApi(ctx)
	body, err := bodyFlags(opts)
	if err != nil {
		return 0, err
	}
	if name := str(opts, "name"); name != "" {
		body["name"] = name
	}
	if description := str(opts, "description"); description != "" {
		body["description"] = description
	}
	if toString(body["name"]) == "" {
		return 0, UsageErr(`missing required flag "--name"`, `Pass --name "web" or --file project.json`)
	}
	key := str(opts, "idempotency_key")
	if key == "" {
		key = newUUID()
	}
	if boolean(opts, "dry_run") {
		EmitDryRun(api.Preview("POST", "/v1/projects", nil, body, key), ctx, opts)
		return 0, nil
	}
	project, err := api.Post("/v1/projects", body, key)
	if err != nil {
		return 0, err
	}
	EmitObject(shape(project, true, nil), ctx, opts, getFields)
	return 0, nil
}

func projectUpdateRun(ctx *Context, opts map[string]any, positionals []string) (int, error) {
	api := NewApi(ctx)
	patch, err := patchFromFlags(opts)
	if err != nil {
		return 0, err
	}
	if len(patch) == 0 {
		return 0, UsageErr("nothing to update", "Pass --set key=value or --unset key")
	}
	project, err := resolveProject(api, positionals[0])
	if err != nil {
		return 0, err
	}
	if boolean(opts, "dry_run") {
		EmitDryRun(api.Preview("PATCH", projectPath(toString(project["id"])), nil, patch, ""), ctx, opts)
		return 0, nil
	}
	updated, err := api.Patch(projectPath(toString(project["id"])), patch)
	if err != nil {
		return 0, err
	}
	EmitObject(shape(updated, true, nil), ctx, opts, getFields)
	return 0, nil
}

func confirmDelete(ctx *Context, project map[string]any) error {
	if ctx.Output != "table" || !stdinIsTTY() {
		return newError("confirmation_required",
			fmt.Sprintf("Refusing to delete project %q (%v) without --yes", toString(project["name"]), project["id"]),
			fmt.Sprintf("Re-run with --yes to delete project %v", project["id"]))
	}
	PrintErr(fmt.Sprintf("About to delete project %q (%v)", toString(project["name"]), project["id"]))
	PrintErr(fmt.Sprintf("target: profile %s, %s, org %s, project %s, API %s",
		ctx.Profile, ctx.BaseURL, ctx.Org, ctx.Project, ctx.APIVersion))
	fmt.Fprint(os.Stderr, "Continue? [y/N] ")
	reader := bufioNewReader()
	answer, _ := reader.ReadString('\n')
	answer = strings.ToLower(strings.TrimSpace(answer))
	if answer != "y" && answer != "yes" {
		return newError("confirmation_required", "Deletion cancelled", "No changes were made")
	}
	return nil
}

func projectDeleteRun(ctx *Context, opts map[string]any, positionals []string) (int, error) {
	api := NewApi(ctx)
	project, err := resolveProject(api, positionals[0])
	if err != nil {
		return 0, err
	}
	if boolean(opts, "dry_run") {
		EmitDryRun(api.Preview("DELETE", projectPath(toString(project["id"])), nil, nil, ""), ctx, opts)
		return 0, nil
	}
	if !boolean(opts, "yes") {
		if err := confirmDelete(ctx, project); err != nil {
			return 0, err
		}
	}
	result, err := api.Delete(projectPath(toString(project["id"])))
	if err != nil {
		return 0, err
	}
	EmitAction(result, ctx, fmt.Sprintf("Deleted project %v.", project["id"]))
	return 0, nil
}

func projectSpecs() []*Spec {
	return []*Spec{
		{
			Path: []string{"project"}, Summary: "Work with projects", Group: true,
			Description: "Create, inspect, update, and delete projects.",
		},
		{
			Path: []string{"project", "list"}, Summary: "List projects", Data: true,
			Description: "List projects in the current org. Returns summary fields; use --full for full objects.",
			Flags: []Flag{
				flag("--limit", "value", "Results per page", "<n>", "50", "", "", false),
				flag("--cursor", "value", "Continue after this cursor", "<cursor>", "", "", "", false),
				flag("--all", "bool", "Fetch every page (cap: 10,000)", "", "", "", "", false),
				flag("--sort", "value", "Sort field; prefix - for descending", "<field>", "", "", "", false),
				flag("--filter", "value", "Exact match filter", "<key=value>", "", "", "", true),
				flag("--search", "value", "Server-side text search", "<text>", "", "", "", false),
				flag("--status", "value", "Filter by status: active, paused, archived", "<status>", "", "", "", false),
				flag("--owner", "value", "Filter by owner email", "<email>", "", "", "", false),
				flag("--since", "value", "Created at or after (RFC 3339 or 24h)", "<time>", "", "", "", false),
				flag("--until", "value", "Created at or before (RFC 3339 or 24h)", "<time>", "", "", "", false),
				flag("--fields", "value", "Project top-level keys", "<id,name,status>", "", "", "", false),
				flag("--full", "bool", "Return full objects instead of summaries", "", "", "", "", false),
			},
			Examples: []string{
				"acme project list --limit 5",
				"acme project list --status active --sort -created_at --json",
				"acme project list --all --fields id,name",
			},
			Related: []string{"acme project get <id>", "acme project create --name web"},
			Run:     projectListRun,
		},
		{
			Path: []string{"project", "get"}, Summary: "Get one project", Data: true,
			Description: "Get one project by ID or unique name. Name ambiguity exits 11 with candidates.",
			Arguments:   []Argument{{Name: "project", Description: "Project ID or name", Required: true}},
			Flags: []Flag{
				flag("--fields", "value", "Project top-level keys", "<id,name,status>", "", "", "", false),
			},
			Examples: []string{"acme project get prj_001", "acme project get web --json"},
			Related:  []string{"acme project list", "acme project update <id> --set status=paused"},
			Run:      projectGetRun,
		},
		{
			Path: []string{"project", "create"}, Summary: "Create a project", Data: true,
			Description: "Create a project. Sends an Idempotency-Key so retries never duplicate it.",
			Flags: []Flag{
				flag("--name", "value", "Project name (required)", "<name>", "", "", "", false),
				flag("--description", "value", "Project description", "<text>", "", "", "", false),
				flag("--file", "value", "JSON body file, or - for stdin", "<path>", "", "", "", false),
				flag("--data", "value", "Inline JSON body", "<json>", "", "", "", false),
				flag("--idempotency-key", "value", "Reuse an external idempotency key", "<key>", "", "", "", false),
			},
			Examples: []string{
				"acme project create --name web",
				`acme project create --name web --description "Customer-facing app" --json`,
				"acme project create --file project.json --dry-run",
			},
			Related: []string{"acme project list", "acme project delete <id> --yes"},
			Run:     projectCreateRun,
		},
		{
			Path: []string{"project", "update"}, Summary: "Update a project", Data: true,
			Description: "Update only the fields you pass. Use --set key=value and --unset key.",
			Arguments:   []Argument{{Name: "project", Description: "Project ID or name", Required: true}},
			Flags: []Flag{
				flag("--set", "value", "Set a field (repeatable, dotted keys allowed)", "<key=value>", "", "", "", true),
				flag("--unset", "value", "Clear a field", "<key>", "", "", "", true),
				flag("--file", "value", "JSON patch file, or - for stdin", "<path>", "", "", "", false),
				flag("--data", "value", "Inline JSON patch", "<json>", "", "", "", false),
			},
			Examples: []string{
				"acme project update prj_001 --set status=paused",
				`acme project update web --set description="New copy" --unset settings.region --json`,
			},
			Related: []string{"acme project get <id>", "acme project delete <id> --yes"},
			Run:     projectUpdateRun,
		},
		{
			Path: []string{"project", "delete"}, Summary: "Delete a project", Data: true, Destructive: true,
			Description: "Delete a project and everything it owns. Destructive: needs --yes off a TTY.",
			Arguments:   []Argument{{Name: "project", Description: "Project ID or name", Required: true}},
			Examples:    []string{"acme project delete prj_001 --yes", "acme project delete web --dry-run --json"},
			Related:     []string{"acme project list", "acme project get <id>"},
			Run:         projectDeleteRun,
		},
	}
}

// helpers used above
func isLowerASCII(text string) bool {
	for _, char := range text {
		if char > unicode.MaxASCII || (char < 'a' || char > 'z') && (char < '0' || char > '9') && char != '-' {
			return false
		}
	}
	return true
}

func sortedStrings(values []string) []string {
	out := append([]string{}, values...)
	sort.Strings(out)
	return out
}

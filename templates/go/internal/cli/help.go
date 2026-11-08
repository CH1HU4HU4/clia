package cli

import (
	"fmt"
	"os"
	"strings"
)

var rootOrder = []string{"auth", "config", "project", "whoami", "version", "completion", "schema", "help"}

const exitLine = "0 success, 2 usage, 3 auth, 4 forbidden, 5 not found, 6 conflict, " +
	"7 rate limit/server, 8 network, 10 confirmation, 11 ambiguous"

func flagSyntax(item Flag) string {
	text := item.Long
	if item.Kind == "value" {
		metavar := item.Metavar
		if metavar == "" {
			metavar = "<value>"
		}
		text += " " + metavar
	}
	if item.Short != "" {
		text = item.Short + ", " + text
	}
	return text
}

func flagLine(item Flag) string {
	extras := []string{}
	if item.Kind == "value" && item.Default != "" {
		extras = append(extras, "default: "+item.Default)
	}
	if item.Env != "" {
		extras = append(extras, "env: "+item.Env)
	}
	description := item.Desc
	if len(extras) > 0 {
		description = strings.TrimSpace(fmt.Sprintf("%s (%s)", description, strings.Join(extras, "; ")))
	}
	return "  " + pad(flagSyntax(item), 30) + description
}

func targetLine() string {
	configured := false
	if _, err := os.Stat(ConfigPath()); err == nil {
		configured = true
	}
	if env("PROFILE") != "" || env("BASE_URL") != "" {
		configured = true
	}
	if !configured {
		return ""
	}
	data, err := LoadConfig()
	if err != nil {
		return ""
	}
	profile := first(env("PROFILE"), data.Profile, "default")
	values := profileValues(data, profile)
	if values == nil {
		values = map[string]string{}
	}
	return fmt.Sprintf("Profile: %s (%s, org %s, project %s, API %s)", profile,
		first(env("BASE_URL"), values["base_url"], "-"),
		first(env("ORG"), values["org"], "-"),
		first(env("PROJECT"), values["project"], "-"),
		first(env("API_VERSION"), values["api_version"], "-"))
}

func globalForHelp() []Flag {
	out := []Flag{}
	for _, item := range GlobalFlags {
		if item.Long != "--version" {
			out = append(out, item)
		}
	}
	return out
}

// RootHelp is the agent-facing front door.
func RootHelp(specs map[string]*Spec) string {
	lines := []string{
		fmt.Sprintf("%s %s — Command line for Acme", Tool, Version),
		"",
		"Manage Acme projects from a terminal or an agent.",
		"",
		"Usage:",
		"  " + Tool + " <command> [flags]",
		"",
		"Commands:",
	}
	top := map[string]bool{}
	for key := range specs {
		if !strings.Contains(key, " ") {
			top[key] = true
		}
	}
	ordered := []string{}
	for _, name := range rootOrder {
		if top[name] {
			ordered = append(ordered, name)
			delete(top, name)
		}
	}
	for name := range top {
		ordered = append(ordered, name)
	}
	for _, name := range ordered {
		lines = append(lines, "  "+pad(name, 12)+specs[name].Summary)
	}
	lines = append(lines, "", "Global flags:")
	for _, item := range globalForHelp() {
		lines = append(lines, flagLine(item))
	}
	lines = append(lines,
		"",
		"Examples:",
		"  "+Tool+" auth login --token $"+EnvPrefix+"_TOKEN",
		"  "+Tool+" project list --limit 5 --json",
		"  "+Tool+" project get prj_001",
		"",
		"Exit codes:",
		"  "+exitLine,
		"",
		"Docs: "+DocsURL,
	)
	if target := targetLine(); target != "" {
		lines = append(lines[:4], append([]string{target, ""}, lines[4:]...)...)
	}
	return strings.Join(lines, "\n")
}

// CommandHelp is generated from the spec; examples are fixtures.
func CommandHelp(spec *Spec, specs map[string]*Spec) string {
	description := spec.Description
	if description == "" {
		description = spec.Summary
	}
	lines := []string{description, ""}
	if spec.Group {
		lines = append(lines, "Usage:", "  "+Tool+" "+strings.Join(spec.Path, " ")+" <command> [flags]", "", "Commands:")
		prefix := strings.Join(spec.Path, " ") + " "
		for key, child := range specs {
			if strings.HasPrefix(key, prefix) {
				parts := strings.Split(key, " ")
				lines = append(lines, "  "+pad(parts[len(parts)-1], 12)+child.Summary)
			}
		}
		return strings.Join(lines, "\n")
	}
	tail := []string{}
	for _, argument := range spec.Arguments {
		if argument.Required {
			tail = append(tail, "<"+argument.Name+">")
		} else {
			tail = append(tail, "["+argument.Name+"]")
		}
	}
	tail = append(tail, "[flags]")
	lines = append(lines, "Usage:", "  "+Tool+" "+strings.Join(spec.Path, " ")+" "+strings.Join(tail, " "), "")
	if len(spec.Arguments) > 0 {
		lines = append(lines, "Arguments:")
		for _, argument := range spec.Arguments {
			lines = append(lines, "  "+pad(argument.Name, 14)+argument.Description)
		}
		lines = append(lines, "")
	}
	lines = append(lines, "Flags:")
	for _, item := range append(append([]Flag{}, spec.Flags...), globalForHelp()...) {
		lines = append(lines, flagLine(item))
	}
	lines = append(lines, "", "Examples:")
	for _, example := range spec.Examples {
		lines = append(lines, "  "+example)
	}
	if len(spec.Related) > 0 {
		lines = append(lines, "", "Related:")
		for _, item := range spec.Related {
			lines = append(lines, "  "+item)
		}
	}
	return strings.Join(lines, "\n")
}

package cli

import (
	"fmt"
	"sort"
	"strings"
)

func metaVersionRun(ctx *Context, opts map[string]any, _ []string) (int, error) {
	PrintText(Version)
	return 0, nil
}

func completionWords(specs map[string]*Spec) []string {
	words := []string{}
	for key, spec := range specs {
		if !spec.Group {
			words = append(words, key)
		}
	}
	sort.Strings(words)
	return words
}

func completionFlags(specs map[string]*Spec) []string {
	seen := map[string]bool{}
	for _, item := range GlobalFlags {
		seen[item.Long] = true
	}
	for _, spec := range specs {
		for _, item := range spec.Flags {
			seen[item.Long] = true
		}
	}
	flags := []string{}
	for name := range seen {
		flags = append(flags, name)
	}
	sort.Strings(flags)
	return flags
}

func completionRun(ctx *Context, opts map[string]any, positionals []string) (int, error) {
	specs := AllSpecs()
	words := completionWords(specs)
	flags := completionFlags(specs)
	switch positionals[0] {
	case "bash":
		PrintText("_" + Tool + "_completions() {\n" +
			"  local cur=\"${COMP_WORDS[COMP_CWORD]}\"\n" +
			"  local words=\"" + strings.Join(words, " ") + "\"\n" +
			"  local flags=\"" + strings.Join(flags, " ") + "\"\n" +
			"  COMPREPLY=( $(compgen -W \"$words $flags\" -- \"$cur\") )\n" +
			"}\n" +
			"complete -F _" + Tool + "_completions " + Tool)
	case "zsh":
		PrintText("#compdef " + Tool + "\n" +
			"_" + Tool + "() {\n" +
			"  local -a words\n" +
			"  words=(" + strings.Join(words, " ") + ")\n" +
			"  _describe 'command' words\n" +
			"}\n" +
			"_" + Tool)
	case "fish":
		lines := []string{"# fish completions for " + Tool}
		for _, word := range words {
			parts := strings.Split(word, " ")
			if len(parts) == 1 {
				lines = append(lines, "complete -c "+Tool+" -f -a "+parts[0])
			} else {
				lines = append(lines, "complete -c "+Tool+" -f -n '__fish_seen_subcommand_from "+
					parts[0]+"' -a "+parts[1])
			}
		}
		PrintText(strings.Join(lines, "\n"))
	default:
		return 0, UsageErr(fmt.Sprintf("unknown shell %q", positionals[0]), "Use bash, zsh, or fish")
	}
	return 0, nil
}

func flagPayload(item Flag) map[string]any {
	payload := map[string]any{
		"name":        item.Long,
		"type":        item.Kind,
		"description": item.Desc,
	}
	if item.Metavar != "" {
		payload["metavar"] = item.Metavar
	}
	if item.Default != "" {
		payload["default"] = item.Default
	}
	if item.Env != "" {
		payload["env"] = item.Env
	}
	if item.Short != "" {
		payload["short"] = item.Short
	}
	return payload
}

func schemaRun(ctx *Context, opts map[string]any, _ []string) (int, error) {
	specs := AllSpecs()
	keys := []string{}
	for key := range specs {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	commands := []any{}
	for _, key := range keys {
		spec := specs[key]
		if spec.Group {
			continue
		}
		flags := []any{}
		for _, item := range spec.Flags {
			flags = append(flags, flagPayload(item))
		}
		arguments := []any{}
		for _, argument := range spec.Arguments {
			payload := map[string]any{"name": argument.Name, "description": argument.Description}
			if argument.Required {
				payload["required"] = true
			}
			arguments = append(arguments, payload)
		}
		examples := []any{}
		for _, example := range spec.Examples {
			examples = append(examples, example)
		}
		commands = append(commands, map[string]any{
			"path":        spec.Path,
			"summary":     spec.Summary,
			"description": spec.Description,
			"arguments":   arguments,
			"flags":       flags,
			"examples":    examples,
			"data":        spec.Data,
			"destructive": spec.Destructive,
		})
	}
	global := []any{}
	for _, item := range GlobalFlags {
		global = append(global, flagPayload(item))
	}
	PrintJSON(map[string]any{
		"name":         Tool,
		"version":      Version,
		"global_flags": global,
		"commands":     commands,
	})
	return 0, nil
}

func helpRun(ctx *Context, opts map[string]any, positionals []string) (int, error) {
	specs := AllSpecs()
	if len(positionals) == 0 {
		PrintText(RootHelp(specs))
		return 0, nil
	}
	spec, ok := specs[strings.Join(positionals, " ")]
	if !ok {
		return 0, UsageErr(fmt.Sprintf("unknown command %q", strings.Join(positionals, " ")), "Run acme --help")
	}
	PrintText(CommandHelp(spec, specs))
	return 0, nil
}

func metaSpecs() []*Spec {
	return []*Spec{
		{Path: []string{"version"}, Summary: "Print the version",
			Description: "Print the semantic version and nothing else.",
			Examples:    []string{"acme version", "acme --version"}, Run: metaVersionRun},
		{Path: []string{"completion"}, Summary: "Generate shell completions",
			Description: "Print a completion script for bash, zsh, or fish.",
			Arguments:   []Argument{{Name: "shell", Description: "bash, zsh, or fish", Required: true}},
			Examples:    []string{"acme completion bash", "acme completion zsh > ~/.zsh/completions/_acme"},
			Run:         completionRun},
		{Path: []string{"schema"}, Summary: "Describe the command tree",
			Description: "Print the command tree, arguments, flags, defaults, and examples as one JSON document.",
			Examples:    []string{"acme schema", "acme schema | jq '.commands[].path'"},
			Run:         schemaRun},
		{Path: []string{"help"}, Summary: "Show help",
			Description: "Show root help or help for one command.",
			Arguments: []Argument{
				{Name: "command", Description: "Command path"},
				{Name: "subcommand", Description: "Subcommand"},
			},
			Examples: []string{"acme help", "acme help project list"}, Run: helpRun},
	}
}

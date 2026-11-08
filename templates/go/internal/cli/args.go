package cli

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
)

// Flag describes one long option. Short forms are optional.
type Flag struct {
	Long    string
	Kind    string // "bool" or "value"
	Desc    string
	Metavar string
	Default string
	Env     string
	Short   string
	Repeat  bool
}

// Argument is one positional.
type Argument struct {
	Name        string
	Description string
	Required    bool
}

// Spec is one command or group, registered once.
type Spec struct {
	Path        []string
	Summary     string
	Description string
	Arguments   []Argument
	Flags       []Flag
	Examples    []string
	Related     []string
	Data        bool
	Destructive bool
	Group       bool
	Run         func(*Context, map[string]any, []string) (int, error)
}

func flag(long, kind, desc, metavar, defaultValue, env, short string, repeat bool) Flag {
	return Flag{Long: long, Kind: kind, Desc: desc, Metavar: metavar, Default: defaultValue,
		Env: env, Short: short, Repeat: repeat}
}

// GlobalFlags are registered once, on every command.
var GlobalFlags = []Flag{
	flag("--json", "bool", "Print one JSON document on stdout", "", "", "", "", false),
	flag("--quiet", "bool", "Print identifiers only", "", "", "", "", false),
	flag("--no-color", "bool", "Disable ANSI color (also NO_COLOR)", "", "", "", "", false),
	flag("--no-input", "bool", "Fail instead of prompting", "", "", "", "", false),
	flag("--yes", "bool", "Confirm destructive actions without a prompt", "", "", "", "", false),
	flag("--dry-run", "bool", "Print the request and send nothing", "", "", "", "", false),
	flag("--debug", "bool", "Verbose logs to stderr, redacted", "", "", "", "", false),
	flag("--timeout", "value", "Request timeout in seconds", "<seconds>", "30", "ACME_TIMEOUT", "", false),
	flag("--profile", "value", "Config profile", "<name>", "", "ACME_PROFILE", "", false),
	flag("--org", "value", "Override the org for this command", "<id>", "", "ACME_ORG", "", false),
	flag("--project", "value", "Override the project for this command", "<id>", "", "ACME_PROJECT", "", false),
	flag("--api-version", "value", "Override the pinned API version", "<version>", "", "ACME_API_VERSION", "", false),
	flag("--base-url", "value", "Override the API base URL", "<url>", "", "ACME_BASE_URL", "", false),
	flag("--allow-http", "bool", "Allow plain http for a non-loopback host", "", "", "", "", false),
	flag("--token", "value", "API token (prefer ACME_TOKEN)", "<token>", "", "ACME_TOKEN", "", false),
	flag("--help", "bool", "Show help", "", "", "", "-h", false),
	flag("--version", "bool", "Print the version (root command only)", "", "", "", "", false),
}

func optionKey(name string) string {
	return strings.ReplaceAll(strings.TrimLeft(name, "-"), "-", "_")
}

type occurrence struct {
	def   *Flag
	name  string
	value any
}

func indexFlags(specs map[string]*Spec) (map[string]*Flag, map[string]*Flag) {
	byLong := map[string]*Flag{}
	byShort := map[string]*Flag{}
	all := [][]Flag{GlobalFlags}
	for _, spec := range specs {
		all = append(all, spec.Flags)
	}
	for _, group := range all {
		for index := range group {
			item := &group[index]
			if _, ok := byLong[item.Long]; !ok {
				byLong[item.Long] = item
			}
			if item.Short != "" {
				if _, ok := byShort[item.Short]; !ok {
					byShort[item.Short] = item
				}
			}
		}
	}
	return byLong, byShort
}

func tokenize(argv []string, byLong, byShort map[string]*Flag) ([]occurrence, []string, error) {
	occurrences := []occurrence{}
	words := []string{}
	afterDashdash := false
	for index := 0; index < len(argv); index++ {
		token := argv[index]
		if afterDashdash {
			words = append(words, token)
			continue
		}
		if token == "--" {
			afterDashdash = true
			continue
		}
		if strings.HasPrefix(token, "--") {
			name := token
			inline := ""
			hasInline := false
			if equals := strings.Index(token, "="); equals >= 0 {
				name = token[:equals]
				inline = token[equals+1:]
				hasInline = true
			}
			definition, ok := byLong[name]
			if !ok && strings.HasPrefix(name, "--no-") {
				base := "--" + name[5:]
				if candidate, found := byLong[base]; found && candidate.Kind == "bool" {
					occurrences = append(occurrences, occurrence{def: candidate, name: base, value: false})
					continue
				}
			}
			if !ok {
				guess := suggest(name, sortedKeys(byLong))
				hint := ""
				if guess != "" {
					hint = fmt.Sprintf("did you mean %q?", guess)
				}
				return nil, nil, UsageErr(fmt.Sprintf("unknown flag %q", name), hint)
			}
			if definition.Kind == "value" {
				value := inline
				if !hasInline {
					if index+1 >= len(argv) {
						return nil, nil, UsageErr("Flag "+name+" needs a value", "Pass "+name+" <value>")
					}
					index++
					value = argv[index]
				}
				occurrences = append(occurrences, occurrence{def: definition, name: name, value: value})
			} else {
				value := any(true)
				if hasInline {
					switch strings.ToLower(inline) {
					case "1", "true", "yes", "on":
						value = true
					case "0", "false", "no", "off":
						value = false
					default:
						return nil, nil, UsageErr(fmt.Sprintf("Flag %s takes true or false, got %q", name, inline), "")
					}
				}
				occurrences = append(occurrences, occurrence{def: definition, name: name, value: value})
			}
			continue
		}
		if strings.HasPrefix(token, "-") && token != "-" {
			definition, ok := byShort[token]
			if !ok {
				return nil, nil, UsageErr(fmt.Sprintf("unknown flag %q", token), "Run acme --help for global flags")
			}
			if definition.Kind == "value" {
				if index+1 >= len(argv) {
					return nil, nil, UsageErr("Flag "+token+" needs a value", "Pass "+token+" <value>")
				}
				index++
				occurrences = append(occurrences, occurrence{def: definition, name: definition.Long, value: argv[index]})
			} else {
				occurrences = append(occurrences, occurrence{def: definition, name: definition.Long, value: true})
			}
			continue
		}
		words = append(words, token)
	}
	return occurrences, words, nil
}

func sortedKeys(items map[string]*Flag) []string {
	keys := []string{}
	for key := range items {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}

func levenshtein(left, right string) int {
	if left == right {
		return 0
	}
	previous := make([]int, len(right)+1)
	for index := range previous {
		previous[index] = index
	}
	for i := 1; i <= len(left); i++ {
		current := make([]int, len(right)+1)
		current[0] = i
		for j := 1; j <= len(right); j++ {
			cost := 1
			if left[i-1] == right[j-1] {
				cost = 0
			}
			current[j] = min3(previous[j]+1, current[j-1]+1, previous[j-1]+cost)
		}
		previous = current
	}
	return previous[len(right)]
}

func min3(a, b, c int) int {
	if a < b {
		if a < c {
			return a
		}
		return c
	}
	if b < c {
		return b
	}
	return c
}

func suggest(word string, candidates []string) string {
	best := ""
	bestDistance := 99
	for _, candidate := range candidates {
		distance := levenshtein(word, candidate)
		if distance < bestDistance {
			best = candidate
			bestDistance = distance
		}
	}
	if best != "" && bestDistance <= maxInt(2, len(word)/3+1) {
		return best
	}
	return ""
}

func maxInt(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func matchCommand(words []string, specs map[string]*Spec) (*Spec, int, error) {
	if len(words) == 0 {
		return nil, 0, nil
	}
	if len(words) >= 2 {
		if spec, ok := specs[words[0]+" "+words[1]]; ok {
			return spec, 2, nil
		}
	}
	if spec, ok := specs[words[0]]; ok {
		return spec, 1, nil
	}
	top := []string{}
	for key := range specs {
		if !strings.Contains(key, " ") {
			top = append(top, key)
		}
	}
	sort.Strings(top)
	guess := suggest(words[0], top)
	hint := ""
	if guess != "" {
		hint = fmt.Sprintf("did you mean %q?", guess)
	}
	return nil, 0, UsageErr(fmt.Sprintf("unknown command %q", strings.Join(words[:minInt(2, len(words))], " ")), hint)
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// Parse returns the matched spec, options, and positionals.
func Parse(argv []string, specs map[string]*Spec) (*Spec, map[string]any, []string, error) {
	byLong, byShort := indexFlags(specs)
	occurrences, words, err := tokenize(argv, byLong, byShort)
	if err != nil {
		return nil, nil, nil, err
	}
	spec, consumed, err := matchCommand(words, specs)
	if err != nil {
		return nil, nil, nil, err
	}
	positionals := words[consumed:]
	if spec != nil && spec.Group && len(positionals) > 0 {
		children := []string{}
		prefix := strings.Join(spec.Path, " ") + " "
		for key := range specs {
			if strings.HasPrefix(key, prefix) {
				parts := strings.Split(key, " ")
				children = append(children, parts[len(parts)-1])
			}
		}
		guess := suggest(positionals[0], children)
		hint := ""
		if guess != "" {
			hint = fmt.Sprintf("did you mean %q?", spec.Path[0]+" "+guess)
		}
		return nil, nil, nil, UsageErr(
			fmt.Sprintf("unknown command %q", strings.Join(append(append([]string{}, spec.Path...), positionals[0]), " ")), hint)
	}

	allowed := append([]Flag{}, GlobalFlags...)
	if spec != nil {
		allowed = append(allowed, spec.Flags...)
	}
	allowedLongs := map[string]bool{}
	opts := map[string]any{}
	for _, item := range allowed {
		allowedLongs[item.Long] = true
		if item.Repeat {
			opts[optionKey(item.Long)] = []string{}
		} else if item.Kind == "bool" {
			opts[optionKey(item.Long)] = false
		} else {
			opts[optionKey(item.Long)] = item.Default
		}
	}
	for _, item := range occurrences {
		if item.def == nil || !allowedLongs[item.def.Long] {
			guess := suggest(item.name, mapKeys(allowedLongs))
			hint := ""
			if guess != "" {
				hint = fmt.Sprintf("did you mean %q?", guess)
			}
			return nil, nil, nil, UsageErr(fmt.Sprintf("unknown flag %q", item.name), hint)
		}
		key := optionKey(item.def.Long)
		if item.def.Repeat {
			values, _ := opts[key].([]string)
			text, _ := item.value.(string)
			opts[key] = append(values, text)
		} else {
			opts[key] = item.value
		}
	}

	if help, _ := opts["help"].(bool); help {
		return spec, opts, positionals, nil
	}
	if spec != nil {
		required := 0
		for _, argument := range spec.Arguments {
			if argument.Required {
				required++
			}
		}
		if len(positionals) > len(spec.Arguments) {
			return nil, nil, nil, UsageErr(
				fmt.Sprintf("unexpected argument %q", positionals[len(spec.Arguments)]),
				"Usage: acme "+strings.Join(spec.Path, " ")+" "+usageTail(spec))
		}
		if len(positionals) < required {
			missing := spec.Arguments[len(positionals)].Name
			return nil, nil, nil, UsageErr("missing required argument <"+missing+">",
				"Usage: acme "+strings.Join(spec.Path, " ")+" "+usageTail(spec))
		}
	}
	return spec, opts, positionals, nil
}

func mapKeys(items map[string]bool) []string {
	keys := []string{}
	for key := range items {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	return keys
}

func usageTail(spec *Spec) string {
	parts := []string{}
	for _, argument := range spec.Arguments {
		if argument.Required {
			parts = append(parts, "<"+argument.Name+">")
		} else {
			parts = append(parts, "["+argument.Name+"]")
		}
	}
	parts = append(parts, "[flags]")
	return strings.Join(parts, " ")
}

func str(opts map[string]any, key string) string {
	return optString(opts, key)
}

func boolean(opts map[string]any, key string) bool {
	return optBool(opts, key)
}

func stringSlice(opts map[string]any, key string) []string {
	values, _ := opts[key].([]string)
	return values
}

func intValue(text string) (int, error) {
	return strconv.Atoi(text)
}

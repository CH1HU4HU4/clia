package cli

import (
	"fmt"
	"os"
	"strings"
)

var configKeys = []string{"profile", "base_url", "api_version", "org", "project", "output",
	"access_token", "refresh_token", "expires_at"}

var configEnv = map[string]string{
	"base_url":     EnvPrefix + "_BASE_URL",
	"api_version":  EnvPrefix + "_API_VERSION",
	"org":          EnvPrefix + "_ORG",
	"project":      EnvPrefix + "_PROJECT",
	"output":       EnvPrefix + "_OUTPUT",
	"profile":      EnvPrefix + "_PROFILE",
	"access_token": EnvPrefix + "_TOKEN",
}

func normalizeConfigKey(key string) string {
	return strings.ReplaceAll(key, "-", "_")
}

func validateConfigKey(key string) (string, error) {
	normalized := normalizeConfigKey(key)
	for _, candidate := range configKeys {
		if candidate == normalized {
			return normalized, nil
		}
	}
	return "", UsageErr(fmt.Sprintf("unknown config key %q", normalized), "Allowed: "+strings.Join(configKeys, ", "))
}

func validateConfigValue(key, value string) error {
	switch key {
	case "output":
		if value != "table" && value != "json" && value != "quiet" {
			return UsageErr("output must be table, json, or quiet", fmt.Sprintf("Got %q", value))
		}
	case "base_url":
		if !strings.HasPrefix(value, "http://") && !strings.HasPrefix(value, "https://") {
			return UsageErr("base_url must start with http:// or https://", fmt.Sprintf("Got %q", value))
		}
	case "profile":
		if value == "" {
			return UsageErr("profile cannot be empty", "")
		}
	}
	return nil
}

func configSource(profile, key string) string {
	if name := configEnv[key]; name != "" && os.Getenv(name) != "" {
		return "env"
	}
	flat := map[string]string{}
	if raw, err := os.ReadFile(ConfigPath()); err == nil {
		flat = ParseTOML(string(raw))
	}
	if key == "profile" {
		if _, ok := flat["profile"]; ok {
			return "file"
		}
	}
	if _, ok := flat["profiles."+profile+"."+key]; ok {
		return "file"
	}
	return "default"
}

func configDisplay(key, value string) string {
	if (key == "access_token" || key == "refresh_token") && value != "" {
		return Mask(value)
	}
	return value
}

func configGetRun(ctx *Context, opts map[string]any, positionals []string) (int, error) {
	key, err := validateConfigKey(positionals[0])
	if err != nil {
		return 0, err
	}
	value := ""
	if key == "profile" {
		value = ctx.Profile
	} else if key == "access_token" && ctx.Token != "" {
		value = ctx.Token
	} else {
		values := profileValues(ctx.Config, ctx.Profile)
		if values == nil {
			values = map[string]string{}
		}
		value = values[key]
	}
	EmitObject(map[string]any{
		"key":     key,
		"value":   configDisplay(key, value),
		"source":  configSource(ctx.Profile, key),
		"profile": ctx.Profile,
	}, ctx, opts, [][2]string{{"key", "key"}, {"value", "value"}, {"source", "source"}, {"profile", "profile"}})
	return 0, nil
}

func configSetRun(ctx *Context, opts map[string]any, positionals []string) (int, error) {
	key, err := validateConfigKey(positionals[0])
	if err != nil {
		return 0, err
	}
	value := positionals[1]
	if err := validateConfigValue(key, value); err != nil {
		return 0, err
	}
	if err := setConfigValue(ctx.Profile, key, value, true); err != nil {
		return 0, err
	}
	EmitObject(map[string]any{"ok": true, "key": key, "profile": ctx.Profile}, ctx, opts,
		[][2]string{{"key", "key"}, {"profile", "profile"}, {"ok", "ok"}})
	return 0, nil
}

func configListRun(ctx *Context, opts map[string]any, _ []string) (int, error) {
	values := profileValues(ctx.Config, ctx.Profile)
	if values == nil {
		values = map[string]string{}
	}
	rows := []map[string]any{}
	for _, key := range configKeys {
		value := values[key]
		if key == "profile" {
			value = ctx.Profile
		} else if key == "access_token" && ctx.Token != "" {
			value = ctx.Token
		}
		rows = append(rows, map[string]any{
			"key":    key,
			"value":  configDisplay(key, value),
			"source": configSource(ctx.Profile, key),
		})
	}
	EmitList(rows, ctx, opts, []Column{
		{Header: "key", Key: "key", Cap: 22},
		{Header: "value", Key: "value", Cap: 50},
		{Header: "source", Key: "source", Cap: 10},
	}, "config keys", false, "", false)
	return 0, nil
}

func configUnsetRun(ctx *Context, opts map[string]any, positionals []string) (int, error) {
	key, err := validateConfigKey(positionals[0])
	if err != nil {
		return 0, err
	}
	if err := unsetConfigValue(ctx.Profile, key); err != nil {
		return 0, err
	}
	EmitObject(map[string]any{"ok": true, "key": key, "profile": ctx.Profile}, ctx, opts,
		[][2]string{{"ok", "ok"}, {"key", "key"}, {"profile", "profile"}})
	return 0, nil
}

func configSpecs() []*Spec {
	return []*Spec{
		{Path: []string{"config"}, Summary: "Read and write CLI configuration", Group: true,
			Description: "Inspect and update the user config. Project config never holds secrets."},
		{Path: []string{"config", "get"}, Summary: "Read a config value", Data: true,
			Description: "Print one resolved config value and its source (flag, env, file, default).",
			Arguments:   []Argument{{Name: "key", Description: "Config key", Required: true}},
			Examples:    []string{"acme config get base-url", "acme config get output --json"},
			Related:     []string{"acme config list", "acme config set <key> <value>"},
			Run:         configGetRun},
		{Path: []string{"config", "set"}, Summary: "Write a config value", Data: true,
			Description: "Write one value to the user config (0600). Creates the profile section if needed.",
			Arguments: []Argument{
				{Name: "key", Description: "Config key", Required: true},
				{Name: "value", Description: "New value", Required: true},
			},
			Examples: []string{"acme config set base-url https://api.acme.com", "acme config set output json --profile ci"},
			Related:  []string{"acme config get <key>", "acme config unset <key>"},
			Run:      configSetRun},
		{Path: []string{"config", "list"}, Summary: "List config values", Data: true,
			Description: "List every known key in the selected profile with its source. Secrets are masked.",
			Examples:    []string{"acme config list", "acme config list --json"},
			Related:     []string{"acme config get <key>", "acme auth status"},
			Run:         configListRun},
		{Path: []string{"config", "unset"}, Summary: "Remove a config value", Data: true,
			Description: "Remove one key from the selected profile and fall back to the default.",
			Arguments:   []Argument{{Name: "key", Description: "Config key", Required: true}},
			Examples:    []string{"acme config unset project", "acme config unset access-token --json"},
			Related:     []string{"acme config list", "acme config get <key>"},
			Run:         configUnsetRun},
	}
}

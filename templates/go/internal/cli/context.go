package cli

import (
	"fmt"
	"os"
)

// Context is the one resolved target: profile, URL, org, project, version, credential.
type Context struct {
	Profile      string
	BaseURL      string
	Org          string
	Project      string
	APIVersion   string
	Output       string
	Token        string
	ExpiresAt    string
	RefreshToken string
	Timeout      float64
	AllowHTTP    bool
	Debug        bool
	Config       *Config
}

func env(name string) string {
	return os.Getenv(EnvPrefix + "_" + name)
}

func first(values ...string) string {
	for _, value := range values {
		if value != "" {
			return value
		}
	}
	return ""
}

func optString(opts map[string]any, key string) string {
	value, ok := opts[key]
	if !ok || value == nil {
		return ""
	}
	text, _ := value.(string)
	return text
}

func optBool(opts map[string]any, key string) bool {
	value, ok := opts[key]
	if !ok {
		return false
	}
	flag, _ := value.(bool)
	return flag
}

// Resolve builds the context from flags, env, config, and defaults, in that order.
func Resolve(opts map[string]any, allowMissingProfile bool) (*Context, error) {
	data, err := LoadConfig()
	if err != nil {
		return nil, err
	}
	explicit := first(optString(opts, "profile"), env("PROFILE"))
	profile := explicit
	if profile == "" {
		profile = data.Profile
	}
	if profile == "" {
		profile = "default"
	}
	values := profileValues(data, profile)
	if values == nil {
		if explicit != "" && !allowMissingProfile {
			known := []string{}
			for name := range data.Profiles {
				known = append(known, name)
			}
			return nil, newError("validation", "Profile "+profile+" is not configured",
				fmt.Sprintf("Configured profiles: %v. Run %s config set profile %s", known, Tool, profile))
		}
		values = map[string]string{}
	}

	ctx := &Context{
		Profile:      profile,
		BaseURL:      first(optString(opts, "base_url"), env("BASE_URL"), values["base_url"], DefaultBaseURL),
		APIVersion:   first(optString(opts, "api_version"), env("API_VERSION"), values["api_version"], DefaultAPIVersion),
		Org:          first(optString(opts, "org"), env("ORG"), values["org"]),
		Project:      first(optString(opts, "project"), env("PROJECT"), values["project"]),
		Output:       first(env("OUTPUT"), values["output"], "table"),
		Token:        first(optString(opts, "token"), env("TOKEN"), env("API_KEY"), values["access_token"]),
		ExpiresAt:    values["expires_at"],
		RefreshToken: values["refresh_token"],
		AllowHTTP:    optBool(opts, "allow_http"),
		Debug:        optBool(opts, "debug"),
		Config:       data,
	}
	if optBool(opts, "json") {
		ctx.Output = "json"
	} else if optBool(opts, "quiet") {
		ctx.Output = "quiet"
	}
	switch ctx.Output {
	case "table", "json", "quiet":
	default:
		return nil, newError("validation", "Unsupported output mode "+ctx.Output, "Use table, json, or quiet")
	}

	timeoutText := first(optString(opts, "timeout"), env("TIMEOUT"), "30")
	var timeout float64
	if _, err := fmt.Sscanf(timeoutText, "%f", &timeout); err != nil || timeout <= 0 {
		return nil, UsageErr("--timeout must be a positive number", "Pass seconds, for example --timeout 30")
	}
	ctx.Timeout = timeout
	return ctx, nil
}

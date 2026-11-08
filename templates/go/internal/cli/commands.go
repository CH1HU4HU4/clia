package cli

func authSpecs() []*Spec {
	return []*Spec{
		{Path: []string{"auth"}, Summary: "Authenticate and inspect credentials", Group: true,
			Description: "Log in, log out, and check the current credential."},
		{Path: []string{"auth", "login"}, Summary: "Log in", Data: true,
			Description: "Store an API token, or run the device flow. Off a TTY, pass --token or --device.",
			Flags:       []Flag{flag("--device", "bool", "Use the OAuth device flow (never prompts)", "", "", "", "", false)},
			Examples:    []string{"acme auth login --token $ACME_TOKEN", "acme auth login --device"},
			Related:     []string{"acme auth status", "acme whoami"},
			Run:         authLoginRun},
		{Path: []string{"auth", "logout"}, Summary: "Log out", Data: true,
			Description: "Remove the stored access and refresh tokens for the selected profile.",
			Examples:    []string{"acme auth logout", "acme auth logout --json"},
			Related:     []string{"acme auth login", "acme auth status"},
			Run:         authLogoutRun},
		{Path: []string{"auth", "status"}, Summary: "Show authentication status", Data: true,
			Description: "Show whether the selected profile is authenticated and which target it uses.",
			Examples:    []string{"acme auth status", "acme auth status --json"},
			Related:     []string{"acme whoami", "acme auth login"},
			Run:         authStatusRun},
	}
}

func whoamiSpec() *Spec {
	return &Spec{
		Path: []string{"whoami"}, Summary: "Show the current user and target", Data: true,
		Description: "Show the user, org, profile, environment, and token expiry for the selected target.",
		Examples:    []string{"acme whoami", "acme whoami --json"},
		Related:     []string{"acme auth status", "acme project list"},
		Run:         whoamiRun,
	}
}

var allSpecCache map[string]*Spec

// AllSpecs registers every command once.
func AllSpecs() map[string]*Spec {
	if allSpecCache != nil {
		return allSpecCache
	}
	specs := map[string]*Spec{}
	groups := [][]*Spec{projectSpecs(), authSpecs(), configSpecs()}
	for _, group := range groups {
		for _, spec := range group {
			key := ""
			for index, part := range spec.Path {
				if index > 0 {
					key += " "
				}
				key += part
			}
			specs[key] = spec
		}
	}
	specs["whoami"] = whoamiSpec()
	for _, spec := range metaSpecs() {
		key := ""
		for index, part := range spec.Path {
			if index > 0 {
				key += " "
			}
			key += part
		}
		specs[key] = spec
	}
	allSpecCache = specs
	return specs
}

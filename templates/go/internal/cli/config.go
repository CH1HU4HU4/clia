package cli

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

// Config is the user config file: context and credentials, always 0600.
type Config struct {
	Profile  string
	Profiles map[string]map[string]string
}

func configHome() string {
	if dir := os.Getenv("XDG_CONFIG_HOME"); dir != "" {
		return dir
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".config")
}

// ConfigPath is the user config path.
func ConfigPath() string {
	return filepath.Join(configHome(), Tool, "config.toml")
}

// ProjectConfigPath is the repo-local context file. It never holds secrets.
func ProjectConfigPath() string {
	cwd, _ := os.Getwd()
	return filepath.Join(cwd, "."+Tool, "config.toml")
}

func defaultConfig() *Config {
	return &Config{
		Profile: "default",
		Profiles: map[string]map[string]string{
			"default": {
				"base_url":    DefaultBaseURL,
				"api_version": DefaultAPIVersion,
				"org":         "",
				"project":     "",
				"output":      "table",
			},
		},
	}
}

func stripComment(line string) string {
	quoted := false
	escaped := false
	for index, char := range line {
		if escaped {
			escaped = false
			continue
		}
		if char == '\\' {
			escaped = true
			continue
		}
		if char == '"' {
			quoted = !quoted
			continue
		}
		if char == '#' && !quoted {
			return line[:index]
		}
	}
	return line
}

func parseValue(raw string) string {
	text := strings.TrimSpace(raw)
	if len(text) >= 2 && strings.HasPrefix(text, "\"") && strings.HasSuffix(text, "\"") {
		if unquoted, err := strconv.Unquote(text); err == nil {
			return unquoted
		}
		return text[1 : len(text)-1]
	}
	return text
}

// ParseTOML reads the flat key/value subset used by the config file.
func ParseTOML(text string) map[string]string {
	data := map[string]string{}
	section := []string{}
	for _, rawLine := range strings.Split(text, "\n") {
		line := strings.TrimSpace(stripComment(rawLine))
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			section = strings.Split(strings.TrimSpace(line[1:len(line)-1]), ".")
			continue
		}
		equals := strings.Index(line, "=")
		if equals < 0 {
			continue
		}
		key := strings.TrimSpace(line[:equals])
		if key == "" {
			continue
		}
		full := append(append([]string{}, section...), key)
		data[strings.Join(full, ".")] = parseValue(line[equals+1:])
	}
	return data
}

// LoadConfig reads the file, refusing a world-readable file with a token.
func LoadConfig() (*Config, error) {
	path := ConfigPath()
	data := defaultConfig()
	info, err := os.Stat(path)
	if err != nil {
		return data, nil
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return data, nil
	}
	if info.Mode().Perm()&0o077 != 0 {
		text := string(raw)
		for _, secret := range []string{"access_token", "refresh_token", "api_key"} {
			if strings.Contains(text, secret) {
				return nil, newError("validation",
					fmt.Sprintf("Refusing to read %s: it is readable by other users and contains a token", path),
					"Run: chmod 600 "+path)
			}
		}
	}
	flat := ParseTOML(string(raw))
	if profile, ok := flat["profile"]; ok {
		data.Profile = profile
	}
	for key, value := range flat {
		if !strings.HasPrefix(key, "profiles.") {
			continue
		}
		parts := strings.SplitN(key, ".", 3)
		if len(parts) != 3 {
			continue
		}
		if data.Profiles[parts[1]] == nil {
			data.Profiles[parts[1]] = map[string]string{}
		}
		data.Profiles[parts[1]][parts[2]] = value
	}
	return data, nil
}

// SaveConfig writes the file at 0600, atomically.
func SaveConfig(data *Config) error {
	path := ConfigPath()
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	flat := map[string]string{"profile": data.Profile}
	for profile, values := range data.Profiles {
		for key, value := range values {
			flat["profiles."+profile+"."+key] = value
		}
	}
	top := []string{}
	sections := map[string]map[string]string{}
	for key, value := range flat {
		if index := strings.LastIndex(key, "."); index >= 0 {
			section := key[:index]
			if sections[section] == nil {
				sections[section] = map[string]string{}
			}
			sections[section][key[index+1:]] = value
		} else {
			top = append(top, key)
		}
	}
	sort.Strings(top)
	lines := []string{}
	for _, key := range top {
		lines = append(lines, fmt.Sprintf("%s = %s", key, strconv.Quote(flat[key])))
	}
	sectionNames := []string{}
	for name := range sections {
		sectionNames = append(sectionNames, name)
	}
	sort.Strings(sectionNames)
	for _, name := range sectionNames {
		if len(lines) > 0 {
			lines = append(lines, "")
		}
		lines = append(lines, "["+name+"]")
		keys := []string{}
		for key := range sections[name] {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		for _, key := range keys {
			lines = append(lines, fmt.Sprintf("%s = %s", key, strconv.Quote(sections[name][key])))
		}
	}
	temp := path + ".tmp"
	if err := os.WriteFile(temp, []byte(strings.Join(lines, "\n")+"\n"), 0o600); err != nil {
		return err
	}
	if err := os.Rename(temp, path); err != nil {
		return err
	}
	return os.Chmod(path, 0o600)
}

func profileValues(data *Config, profile string) map[string]string {
	values, ok := data.Profiles[profile]
	if !ok {
		return nil
	}
	merged := map[string]string{}
	for key, value := range data.Profiles["default"] {
		merged[key] = value
	}
	for key, value := range values {
		merged[key] = value
	}
	return merged
}

func setConfigValue(profile, key, value string, create bool) error {
	data, err := LoadConfig()
	if err != nil {
		return err
	}
	if key == "profile" {
		data.Profile = value
		return SaveConfig(data)
	}
	values := data.Profiles[profile]
	if values == nil {
		if !create {
			return newError("validation", "Profile "+profile+" is not configured",
				fmt.Sprintf("Run: %s config set profile %s", Tool, profile))
		}
		values = map[string]string{}
		data.Profiles[profile] = values
	}
	values[key] = value
	return SaveConfig(data)
}

func unsetConfigValue(profile, key string) error {
	data, err := LoadConfig()
	if err != nil {
		return err
	}
	if key == "profile" {
		data.Profile = "default"
		return SaveConfig(data)
	}
	values := data.Profiles[profile]
	if values == nil {
		return newError("validation", "Profile "+profile+" is not configured", "")
	}
	delete(values, key)
	return SaveConfig(data)
}

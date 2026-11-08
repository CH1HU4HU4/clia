package cli

import (
	"strings"
)

var sensitiveParts = []string{"token", "secret", "password", "key", "authorization", "cookie"}

// Mask keeps a short fingerprint and hides the rest.
func Mask(value string) string {
	if value == "" {
		return value
	}
	if len(value) < 20 {
		return "****"
	}
	return value[:4] + "****" + value[len(value)-4:]
}

func redactValue(key string, value any) any {
	lower := strings.ToLower(key)
	for _, part := range sensitiveParts {
		if strings.Contains(lower, part) {
			return Mask(strings.TrimSpace(toString(value)))
		}
	}
	switch typed := value.(type) {
	case map[string]string:
		out := map[string]string{}
		for nestedKey, nestedValue := range typed {
			out[nestedKey] = toString(redactValue(nestedKey, nestedValue))
		}
		return out
	case map[string]any:
		out := map[string]any{}
		for nestedKey, nestedValue := range typed {
			out[nestedKey] = redactValue(nestedKey, nestedValue)
		}
		return out
	case []any:
		out := make([]any, len(typed))
		for index, item := range typed {
			out[index] = redactValue(key, item)
		}
		return out
	default:
		return value
	}
}

// RedactHeaders masks values whose key looks sensitive.
func RedactHeaders(headers map[string]string) map[string]any {
	out := map[string]any{}
	for key, value := range headers {
		out[key] = redactValue(key, value)
	}
	return out
}

// RedactText replaces known secrets in free text.
func RedactText(text string, secrets ...string) string {
	out := text
	for _, secret := range secrets {
		if secret != "" {
			out = strings.ReplaceAll(out, secret, Mask(secret))
		}
	}
	return out
}

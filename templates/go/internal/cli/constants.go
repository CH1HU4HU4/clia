package cli

const (
	Tool               = "acme"
	EnvPrefix          = "ACME"
	Version            = "1.0.0"
	DocsURL            = "https://example.com/acme/docs/cli"
	DefaultBaseURL     = "https://api.acme.com"
	DefaultAPIVersion  = "2026-01-01"
	DefaultPageSize    = 50
	MaxPageSize        = 200
	AllCap             = 10000
)

func toString(value any) string {
	if text, ok := value.(string); ok {
		return text
	}
	if value == nil {
		return ""
	}
	if text, ok := value.(interface{ String() string }); ok {
		return text.String()
	}
	return ""
}

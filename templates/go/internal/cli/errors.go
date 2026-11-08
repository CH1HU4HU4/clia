package cli

import (
	"encoding/json"
	"fmt"
	"os"
)

var exitByCode = map[string]int{
	"unexpected":            1,
	"job_failed":            1,
	"usage":                 2,
	"auth_required":         3,
	"forbidden":             4,
	"not_found":             5,
	"conflict":              6,
	"validation":            6,
	"rate_limited":          7,
	"server_error":          7,
	"network_error":         8,
	"timeout":               8,
	"partial_success":       9,
	"confirmation_required": 10,
	"ambiguous_target":      11,
	"diagnostic_failed":     12,
	"cancelled":             130,
}

// CLIError is the one error type commands return.
type CLIError struct {
	Code      string
	Message   string
	Hint      string
	Status    int
	Retryable bool
	RequestID string
	Target    map[string]string
	Extra     map[string]any
	Exit      int
}

func (e *CLIError) Error() string { return e.Message }

func newError(code, message, hint string) *CLIError {
	exit, ok := exitByCode[code]
	if !ok {
		exit = 1
	}
	retryable := code == "rate_limited" || code == "server_error" ||
		code == "network_error" || code == "timeout"
	return &CLIError{Code: code, Message: message, Hint: hint, Retryable: retryable, Exit: exit}
}

// UsageErr builds an exit-2 usage error.
func UsageErr(message, hint string) *CLIError {
	return newError("usage", message, hint)
}

func codeForStatus(status int) string {
	switch status {
	case 400, 422:
		return "validation"
	case 401:
		return "auth_required"
	case 403:
		return "forbidden"
	case 404:
		return "not_found"
	case 409:
		return "conflict"
	case 429:
		return "rate_limited"
	}
	if status >= 500 {
		return "server_error"
	}
	if status >= 400 {
		return "validation"
	}
	return "unexpected"
}

func targetDict(ctx *Context) map[string]string {
	if ctx == nil || ctx.Profile == "" {
		return nil
	}
	return map[string]string{
		"profile":     ctx.Profile,
		"base_url":    ctx.BaseURL,
		"org":         ctx.Org,
		"project":     ctx.Project,
		"api_version": ctx.APIVersion,
	}
}

func errorPayload(err *CLIError, ctx *Context) map[string]any {
	target := err.Target
	if target == nil {
		target = targetDict(ctx)
	}
	payload := map[string]any{
		"code":      err.Code,
		"message":   err.Message,
		"retryable": err.Retryable,
	}
	if err.Hint != "" {
		payload["hint"] = err.Hint
	}
	if err.Status != 0 {
		payload["status"] = err.Status
	}
	if err.RequestID != "" {
		payload["request_id"] = err.RequestID
	}
	if target != nil {
		payload["target"] = target
	}
	for key, value := range err.Extra {
		payload[key] = value
	}
	return map[string]any{"error": payload}
}

// EmitError writes the one error representation, never to stdout.
func EmitError(err *CLIError, ctx *Context, jsonMode bool) {
	if jsonMode {
		body, _ := json.Marshal(errorPayload(err, ctx))
		fmt.Fprintln(os.Stderr, string(body))
		return
	}
	fmt.Fprintf(os.Stderr, "error: %s\n", err.Message)
	if err.Hint != "" {
		fmt.Fprintf(os.Stderr, "hint: %s\n", err.Hint)
	}
	target := err.Target
	if target == nil {
		target = targetDict(ctx)
	}
	if target != nil {
		fmt.Fprintf(os.Stderr, "target: profile %s, %s, org %s, project %s, API %s\n",
			target["profile"], target["base_url"], target["org"], target["project"], target["api_version"])
	}
}

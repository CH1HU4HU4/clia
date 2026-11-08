package cli

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"runtime"
	"strconv"
	"strings"
	"time"
)

// Query is an ordered list of query parameters; empty values are skipped.
type Query [][2]string

// Api owns HTTP: URLs, auth headers, retries, refresh, timeouts, error mapping.
type Api struct {
	Ctx       *Context
	Client    *http.Client
	Refreshed bool
	base      *url.URL
}

func NewApi(ctx *Context) *Api {
	transport := http.DefaultTransport.(*http.Transport).Clone()
	transport.Proxy = http.ProxyFromEnvironment
	return &Api{
		Ctx: ctx,
		Client: &http.Client{
			Timeout:   time.Duration(ctx.Timeout * float64(time.Second)),
			Transport: transport,
		},
	}
}

func (api *Api) url(path string, query Query) string {
	base := strings.TrimRight(api.Ctx.BaseURL, "/")
	target := base + path
	values := url.Values{}
	for _, pair := range query {
		if pair[1] == "" {
			continue
		}
		values.Add(pair[0], pair[1])
	}
	if encoded := values.Encode(); encoded != "" {
		target += "?" + encoded
	}
	return target
}

func (api *Api) checkBaseURL() error {
	parsed, err := url.Parse(api.Ctx.BaseURL)
	if err != nil || (parsed.Scheme != "http" && parsed.Scheme != "https") {
		return UsageErr("Base URL must be http or https, got "+api.Ctx.BaseURL,
			"Set --base-url https://api.example.com")
	}
	if parsed.Scheme == "http" && !api.Ctx.AllowHTTP {
		host := parsed.Hostname()
		if host != "localhost" && host != "127.0.0.1" && host != "::1" {
			return UsageErr("Refusing plain http base URL "+api.Ctx.BaseURL,
				"Use https, or pass --allow-http for a trusted loopback host")
		}
	}
	return nil
}

func (api *Api) headers(hasBody bool, idempotencyKey string) map[string]string {
	headers := map[string]string{
		"accept":        "application/json",
		"user-agent":    fmt.Sprintf("%s/%s (%s; %s)", Tool, Version, runtime.GOOS, runtime.GOARCH),
		"x-api-version": api.Ctx.APIVersion,
	}
	if api.Ctx.Token != "" {
		headers["authorization"] = "Bearer " + api.Ctx.Token
	}
	if hasBody {
		headers["content-type"] = "application/json"
	}
	if idempotencyKey != "" {
		headers["idempotency-key"] = idempotencyKey
	}
	return headers
}

// Preview is the redacted structured request for --dry-run.
func (api *Api) Preview(method, path string, query Query, body any, idempotencyKey string) map[string]any {
	return map[string]any{
		"method":  method,
		"url":     api.url(path, query),
		"headers": RedactHeaders(api.headers(body != nil, idempotencyKey)),
		"body":    body,
	}
}

func (api *Api) debug(line string) {
	if !api.Ctx.Debug {
		return
	}
	PrintErr("debug: " + RedactText(line, api.Ctx.Token, api.Ctx.RefreshToken))
}

func parseTime(text string) (time.Time, bool) {
	if text == "" {
		return time.Time{}, false
	}
	parsed, err := time.Parse(time.RFC3339, text)
	if err != nil {
		return time.Time{}, false
	}
	return parsed, true
}

func (api *Api) ensureFresh() error {
	if api.Refreshed || api.Ctx.ExpiresAt == "" || api.Ctx.RefreshToken == "" {
		return nil
	}
	expires, ok := parseTime(api.Ctx.ExpiresAt)
	if !ok {
		return nil
	}
	if time.Until(expires) > 60*time.Second {
		return nil
	}
	api.Refreshed = true
	payload, err := api.rawRequest("POST", "/v1/auth/refresh", nil,
		map[string]any{"refresh_token": api.Ctx.RefreshToken}, "", false)
	if err != nil {
		return newError("auth_required", "Token refresh failed", "Run "+Tool+" auth login")
	}
	token := toString(payload["access_token"])
	if token == "" {
		return newError("auth_required", "Token refresh returned no access token", "Run "+Tool+" auth login")
	}
	api.Ctx.Token = token
	if expiresAt, ok := payload["expires_at"]; ok {
		api.Ctx.ExpiresAt = toString(expiresAt)
	}
	_ = setConfigValue(api.Ctx.Profile, "access_token", token, false)
	if api.Ctx.ExpiresAt != "" {
		_ = setConfigValue(api.Ctx.Profile, "expires_at", api.Ctx.ExpiresAt, false)
	}
	api.debug("token refreshed for profile " + api.Ctx.Profile)
	return nil
}

// Request performs one logical API call with the documented retry policy.
func (api *Api) Request(method, path string, query Query, body any, idempotencyKey string) (map[string]any, error) {
	if err := api.checkBaseURL(); err != nil {
		return nil, err
	}
	if err := api.ensureFresh(); err != nil {
		return nil, err
	}
	return api.rawRequest(method, path, query, body, idempotencyKey, true)
}

func (api *Api) rawRequest(method, path string, query Query, body any, idempotencyKey string, withAuth bool) (map[string]any, error) {
	if withAuth && api.Ctx.Token == "" {
		return nil, newError("auth_required", "No API token configured",
			"Run "+Tool+" auth login, set "+EnvPrefix+"_TOKEN, or pass --token")
	}
	target := api.url(path, query)
	headers := api.headers(body != nil, idempotencyKey)
	if !withAuth {
		delete(headers, "authorization")
	}
	var encoded []byte
	if body != nil {
		encoded, _ = json.Marshal(body)
	}
	api.debug(method + " " + target)
	if api.Ctx.Debug {
		redacted, _ := json.Marshal(RedactHeaders(headers))
		api.debug("headers: " + string(redacted))
	}
	canRetry := withAuth && (method == "GET" || idempotencyKey != "")
	attempt := 0
	for {
		attempt++
		started := time.Now()
		request, err := http.NewRequest(method, target, bytes.NewReader(encoded))
		if err != nil {
			return nil, newError("network_error", "Cannot build request: "+err.Error(), "")
		}
		for key, value := range headers {
			request.Header.Set(key, value)
		}
		response, err := api.Client.Do(request)
		if err != nil {
			var netErr net.Error
			isTimeout := errors.As(err, &netErr) && netErr.Timeout()
			if canRetry && attempt < 3 {
				api.backoff(attempt, "")
				continue
			}
			if isTimeout {
				return nil, newError("timeout", fmt.Sprintf("Request timed out after %vs", api.Ctx.Timeout), "Retry, or raise --timeout")
			}
			return nil, newError("network_error", "Cannot reach "+api.Ctx.BaseURL+": "+err.Error(),
				"Check the base URL and your network")
		}
		raw, _ := io.ReadAll(response.Body)
		response.Body.Close()
		api.debug(fmt.Sprintf("< %d %s (%d ms)", response.StatusCode, method, time.Since(started).Milliseconds()))
		if response.StatusCode >= 200 && response.StatusCode < 300 {
			if len(raw) == 0 {
				return map[string]any{}, nil
			}
			payload := map[string]any{}
			if err := json.Unmarshal(raw, &payload); err != nil {
				return nil, newError("network_error", "Invalid JSON response", "Retry, then run acme doctor")
			}
			return payload, nil
		}
		if (response.StatusCode == 429 || response.StatusCode >= 500) && canRetry && attempt < 3 {
			api.backoff(attempt, response.Header.Get("retry-after"))
			continue
		}
		return nil, api.httpError(response.StatusCode, raw, response.Header)
	}
}

func (api *Api) backoff(attempt int, retryAfter string) {
	delay := 250 * time.Millisecond * time.Duration(1<<uint(attempt-1))
	if retryAfter != "" {
		if seconds, err := strconv.ParseFloat(retryAfter, 64); err == nil {
			minimum := time.Duration(seconds * float64(time.Second))
			if minimum > delay {
				delay = minimum
			}
		}
	}
	if delay > 2*time.Second {
		delay = 2 * time.Second
	}
	api.debug(fmt.Sprintf("retrying in %s", delay))
	time.Sleep(delay)
}

func (api *Api) httpError(status int, raw []byte, headers http.Header) *CLIError {
	code := codeForStatus(status)
	message := fmt.Sprintf("HTTP %d", status)
	hint := ""
	extra := map[string]any{}
	payload := map[string]any{}
	if err := json.Unmarshal(raw, &payload); err == nil {
		if errorObject, ok := payload["error"].(map[string]any); ok {
			if text := toString(errorObject["message"]); text != "" {
				message = text
			}
			if text := toString(errorObject["hint"]); text != "" {
				hint = text
			}
			if versions, ok := errorObject["supported_versions"]; ok {
				extra["supported_versions"] = versions
			}
			if fields, ok := errorObject["fields"]; ok {
				extra["fields"] = fields
			}
		}
	} else if len(raw) > 0 {
		message = strings.TrimSpace(string(raw))
		if len(message) > 300 {
			message = message[:300]
		}
	}
	if status == 429 {
		retryAfter := 1.0
		if header := headers.Get("retry-after"); header != "" {
			if parsed, err := strconv.ParseFloat(header, 64); err == nil {
				retryAfter = parsed
			}
		}
		extra["retry_after"] = retryAfter
		if hint == "" {
			hint = fmt.Sprintf("Retry after %v seconds", retryAfter)
		}
	}
	if code == "auth_required" && hint == "" {
		hint = "Run " + Tool + " auth login"
	}
	err := newError(code, message, hint)
	err.Status = status
	err.RequestID = headers.Get("x-request-id")
	err.Extra = extra
	return err
}

func (api *Api) Get(path string, query Query) (map[string]any, error) {
	return api.Request("GET", path, query, nil, "")
}

func (api *Api) Post(path string, body any, idempotencyKey string) (map[string]any, error) {
	return api.Request("POST", path, nil, body, idempotencyKey)
}

func (api *Api) Patch(path string, body any) (map[string]any, error) {
	return api.Request("PATCH", path, nil, body, "")
}

func (api *Api) Delete(path string) (map[string]any, error) {
	return api.Request("DELETE", path, nil, nil, "")
}

func (api *Api) Me() (map[string]any, error) {
	return api.Get("/v1/me", Query{{"org", api.Ctx.Org}})
}

func (api *Api) PublicPost(path string, body any) (map[string]any, error) {
	if err := api.checkBaseURL(); err != nil {
		return nil, err
	}
	return api.rawRequest("POST", path, nil, body, "", false)
}

func warn(message string) {
	fmt.Fprintln(os.Stderr, "warning: "+message)
}

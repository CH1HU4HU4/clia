package cli

import (
	"fmt"
	"time"
)

func saveCredential(ctx *Context, accessToken, refreshToken, expiresAt string) error {
	if err := setConfigValue(ctx.Profile, "access_token", accessToken, false); err != nil {
		return err
	}
	if refreshToken != "" {
		if err := setConfigValue(ctx.Profile, "refresh_token", refreshToken, false); err != nil {
			return err
		}
	} else {
		_ = unsetConfigValue(ctx.Profile, "refresh_token")
	}
	if expiresAt != "" {
		return setConfigValue(ctx.Profile, "expires_at", expiresAt, false)
	}
	return unsetConfigValue(ctx.Profile, "expires_at")
}

func authLoginRun(ctx *Context, opts map[string]any, _ []string) (int, error) {
	api := NewApi(ctx)
	if boolean(opts, "device") {
		device, err := api.PublicPost("/v1/auth/device", map[string]any{"client": "acme-cli"})
		if err != nil {
			return 0, err
		}
		PrintErr(fmt.Sprintf("Open %v and enter code %v", device["verification_uri"], device["user_code"]))
		interval := 1
		if value, ok := device["interval"].(float64); ok && value > 0 {
			interval = int(value)
		}
		deadline := time.Now().Add(120 * time.Second)
		var token map[string]any
		for time.Now().Before(deadline) {
			token, err = api.PublicPost("/v1/auth/token", map[string]any{"device_code": device["device_code"]})
			if err == nil {
				break
			}
			if cliErr, ok := err.(*CLIError); ok && cliErr.Status == 428 {
				sleepSeconds(interval)
				continue
			}
			return 0, err
		}
		if token == nil {
			return 0, newError("auth_required", "Device login timed out", "Run acme auth login --device again")
		}
		ctx.Token = toString(token["access_token"])
		ctx.RefreshToken = toString(token["refresh_token"])
		ctx.ExpiresAt = toString(token["expires_at"])
		if err := saveCredential(ctx, ctx.Token, ctx.RefreshToken, ctx.ExpiresAt); err != nil {
			return 0, err
		}
	} else {
		token := str(opts, "token")
		if token == "" {
			if !stdinIsTTY() {
				return 0, UsageErr("no token provided", "Pass --token, set ACME_TOKEN, or use --device")
			}
			var err error
			token, err = promptToken()
			if err != nil {
				return 0, UsageErr("could not read the token", "Pass --token instead")
			}
		}
		if token == "" {
			return 0, UsageErr("no token provided", "Pass --token or set ACME_TOKEN")
		}
		ctx.Token = token
		ctx.ExpiresAt = ""
		ctx.RefreshToken = ""
		if err := saveCredential(ctx, token, "", ""); err != nil {
			return 0, err
		}
	}

	me, err := api.Me()
	if err != nil {
		return 0, err
	}
	user := ""
	if account, ok := me["user"].(map[string]any); ok {
		user = toString(account["email"])
	}
	payload := map[string]any{
		"ok":            true,
		"authenticated": true,
		"user":          user,
		"org":           first(toString(me["org"]), ctx.Org),
		"profile":       ctx.Profile,
		"token":         nil,
	}
	if ctx.Output == "json" {
		PrintJSON(payload)
	} else {
		PrintText(fmt.Sprintf("Logged in as %s (org %s, profile %s)", user, payload["org"], ctx.Profile))
	}
	return 0, nil
}

func authLogoutRun(ctx *Context, opts map[string]any, _ []string) (int, error) {
	for _, key := range []string{"access_token", "refresh_token", "expires_at"} {
		_ = unsetConfigValue(ctx.Profile, key)
	}
	payload := map[string]any{"ok": true, "logged_out": true, "profile": ctx.Profile}
	if ctx.Output == "json" {
		PrintJSON(payload)
	} else {
		PrintText("Logged out of profile " + ctx.Profile + ".")
	}
	return 0, nil
}

func authStatusRun(ctx *Context, opts map[string]any, _ []string) (int, error) {
	fields := [][2]string{
		{"authenticated", "authenticated"}, {"profile", "profile"}, {"base_url", "base_url"},
		{"org", "org"}, {"project", "project"}, {"api_version", "api_version"},
		{"environment", "environment"}, {"user", "user"}, {"expires_at", "expires_at"},
	}
	payload := map[string]any{
		"authenticated": false,
		"profile":       ctx.Profile,
		"base_url":      ctx.BaseURL,
		"org":           nullable(ctx.Org),
		"project":       nullable(ctx.Project),
		"api_version":   ctx.APIVersion,
		"environment":   nil,
		"user":          nil,
		"expires_at":    nil,
	}
	if ctx.Token != "" {
		api := NewApi(ctx)
		me, err := api.Me()
		if err != nil {
			return 0, err
		}
		user := ""
		if account, ok := me["user"].(map[string]any); ok {
			user = toString(account["email"])
		}
		payload["authenticated"] = true
		payload["org"] = first(toString(me["org"]), ctx.Org)
		payload["environment"] = me["environment"]
		payload["user"] = user
		payload["expires_at"] = first(ctx.ExpiresAt, toString(me["token_expires_at"]))
		if payload["expires_at"] == "" {
			payload["expires_at"] = nil
		}
	}
	EmitObject(payload, ctx, opts, fields)
	return 0, nil
}

func nullable(value string) any {
	if value == "" {
		return nil
	}
	return value
}

func whoamiRun(ctx *Context, opts map[string]any, _ []string) (int, error) {
	api := NewApi(ctx)
	me, err := api.Me()
	if err != nil {
		return 0, err
	}
	user := ""
	userID := ""
	if account, ok := me["user"].(map[string]any); ok {
		user = toString(account["email"])
		userID = toString(account["id"])
	}
	expires := first(ctx.ExpiresAt, toString(me["token_expires_at"]))
	var expiresValue any
	if expires != "" {
		expiresValue = expires
	}
	payload := map[string]any{
		"user":             user,
		"user_id":          userID,
		"org":              first(toString(me["org"]), ctx.Org),
		"profile":          ctx.Profile,
		"environment":      me["environment"],
		"token_expires_at": expiresValue,
		"base_url":         ctx.BaseURL,
		"api_version":      ctx.APIVersion,
	}
	EmitObject(payload, ctx, opts, [][2]string{
		{"user", "user"}, {"org", "org"}, {"profile", "profile"},
		{"environment", "environment"}, {"token_expires_at", "token_expires_at"},
		{"base_url", "base_url"}, {"api_version", "api_version"},
	})
	return 0, nil
}

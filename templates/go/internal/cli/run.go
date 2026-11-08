package cli

import (
	"fmt"
	"os"
	"os/signal"
	"strings"
)

func jsonWanted(argv []string, opts map[string]any, ctx *Context) bool {
	if opts != nil && boolean(opts, "json") {
		return true
	}
	if ctx != nil && ctx.Output == "json" {
		return true
	}
	if env("OUTPUT") == "json" {
		return true
	}
	for _, arg := range argv {
		if arg == "--json" {
			return true
		}
	}
	return false
}

func failure(err error, ctx *Context, argv []string, opts map[string]any) int {
	cliErr, ok := err.(*CLIError)
	if !ok {
		message := "Internal error"
		if err != nil {
			message = "Internal error: " + err.Error()
		}
		cliErr = newError("unexpected", message, "Run with --debug for a traceback")
	}
	if ctx != nil {
		cliErr.Message = RedactText(cliErr.Message, ctx.Token, ctx.RefreshToken)
		if cliErr.Hint != "" {
			cliErr.Hint = RedactText(cliErr.Hint, ctx.Token, ctx.RefreshToken)
		}
	}
	EmitError(cliErr, ctx, jsonWanted(argv, opts, ctx))
	return cliErr.Exit
}

// Main parses once, resolves one context, runs one command, maps one error.
func Main(argv []string) int {
	interrupts := make(chan os.Signal, 1)
	signal.Notify(interrupts, os.Interrupt)
	go func() {
		<-interrupts
		EmitError(newError("cancelled", "Interrupted", ""), nil, jsonWanted(argv, nil, nil))
		os.Exit(130)
	}()

	specs := AllSpecs()
	spec, opts, positionals, err := Parse(argv, specs)
	if err != nil {
		return failure(err, nil, argv, opts)
	}
	if spec == nil {
		if opts != nil && boolean(opts, "version") {
			PrintText(Version)
			return 0
		}
		PrintText(RootHelp(specs))
		return 0
	}
	if boolean(opts, "help") {
		PrintText(CommandHelp(spec, specs))
		return 0
	}
	if boolean(opts, "version") {
		return failure(UsageErr("--version is a root flag", "Run: "+Tool+" --version"), nil, argv, opts)
	}

	var ctx *Context
	path := strings.Join(spec.Path, " ")
	switch path {
	case "help", "version", "completion", "schema":
		// These work offline and without auth.
	default:
		ctx, err = Resolve(opts, path == "config set")
		if err != nil {
			return failure(err, nil, argv, opts)
		}
	}

	code, err := spec.Run(ctx, opts, positionals)
	if err != nil {
		return failure(err, ctx, argv, opts)
	}
	if ctx != nil && ctx.Debug {
		fmt.Fprintf(os.Stderr, "debug: command %s finished\n", path)
	}
	return code
}

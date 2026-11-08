package main

import (
	"os"

	"acme/internal/cli"
)

func main() {
	os.Exit(cli.Main(os.Args[1:]))
}

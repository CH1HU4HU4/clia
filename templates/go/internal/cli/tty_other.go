//go:build !darwin && !freebsd && !netbsd && !openbsd && !linux && !solaris

package cli

func isTerminal(_ int) bool {
	return false
}

//go:build linux || solaris

package cli

import (
	"syscall"
	"unsafe"
)

func isTerminal(fd int) bool {
	var termios syscall.Termios
	_, _, err := syscall.Syscall6(syscall.SYS_IOCTL, uintptr(fd), uintptr(syscall.TCGETS),
		uintptr(unsafe.Pointer(&termios)), 0, 0, 0)
	return err == 0
}

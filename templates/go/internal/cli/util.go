package cli

import (
	"bufio"
	"fmt"
	"os"
	"time"
)

func bufioNewReader() *bufio.Reader {
	return bufio.NewReader(os.Stdin)
}

func stdinIsTTY() bool {
	return isTerminal(int(os.Stdin.Fd()))
}

func promptToken() (string, error) {
	fmt.Fprint(os.Stderr, "Paste API token: ")
	reader := bufioNewReader()
	text, err := reader.ReadString('\n')
	if err != nil {
		return "", err
	}
	return trimLine(text), nil
}

func trimLine(text string) string {
	for len(text) > 0 && (text[len(text)-1] == '\n' || text[len(text)-1] == '\r') {
		text = text[:len(text)-1]
	}
	return text
}

func sleepSeconds(seconds int) {
	time.Sleep(time.Duration(seconds) * time.Second)
}

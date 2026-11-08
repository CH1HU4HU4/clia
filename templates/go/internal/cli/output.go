package cli

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
)

// Column is one table column. Cap 0 means no truncation.
type Column struct {
	Header string
	Key    string
	Cap    int
}

func PrintJSON(payload any) {
	body, err := json.Marshal(payload)
	if err != nil {
		fmt.Fprintln(os.Stderr, "error: cannot encode JSON:", err)
		return
	}
	fmt.Fprintln(os.Stdout, string(body))
}

func PrintText(text string) {
	fmt.Fprintln(os.Stdout, text)
}

func PrintErr(text string) {
	fmt.Fprintln(os.Stderr, text)
}

func cell(value any, cap int) string {
	if value == nil {
		return "-"
	}
	text := fmt.Sprint(value)
	if cap > 0 && len(text) > cap {
		return text[:cap-1] + "…"
	}
	return text
}

// RenderTable keeps IDs whole and drops width from truncatable columns.
func RenderTable(columns []Column, rows []map[string]any) string {
	widths := make([]int, len(columns))
	for index, column := range columns {
		widths[index] = len(column.Header)
		for _, row := range rows {
			text := cell(row[column.Key], column.Cap)
			if len(text) > widths[index] {
				widths[index] = len(text)
			}
		}
	}
	total := 0
	for _, width := range widths {
		total += width
	}
	total += 3 * (len(columns) - 1)
	if total > 120 {
		excess := total - 120
		for index, column := range columns {
			if column.Cap > 0 && excess > 0 {
				squeeze := excess
				if squeeze > widths[index]-len(column.Header) {
					squeeze = widths[index] - len(column.Header)
				}
				if squeeze > 0 {
					widths[index] -= squeeze
					excess -= squeeze
				}
			}
		}
	}
	headers := make([]string, len(columns))
	for index, column := range columns {
		headers[index] = pad(strings.ToUpper(column.Header), widths[index])
	}
	lines := []string{strings.TrimRight(strings.Join(headers, "   "), " ")}
	for _, row := range rows {
		cells := make([]string, len(columns))
		for index, column := range columns {
			text := cell(row[column.Key], column.Cap)
			if len(text) > widths[index] {
				text = text[:widths[index]-1] + "…"
			}
			cells[index] = pad(text, widths[index])
		}
		lines = append(lines, strings.TrimRight(strings.Join(cells, "   "), " "))
	}
	return strings.Join(lines, "\n")
}

func pad(text string, width int) string {
	if len(text) >= width {
		return text
	}
	return text + strings.Repeat(" ", width-len(text))
}

func ListEnvelope(items []map[string]any, hasMore bool, nextCursor string, truncated bool) map[string]any {
	var cursor any
	if nextCursor != "" {
		cursor = nextCursor
	}
	return map[string]any{
		"data":        items,
		"has_more":    hasMore,
		"next_cursor": cursor,
		"truncated":   truncated,
	}
}

// EmitList writes one page envelope, one ID per line, or a table.
func EmitList(items []map[string]any, ctx *Context, opts map[string]any, columns []Column,
	label string, hasMore bool, nextCursor string, truncated bool) {
	switch ctx.Output {
	case "json":
		PrintJSON(ListEnvelope(items, hasMore, nextCursor, truncated))
		return
	case "quiet":
		for _, item := range items {
			if value, ok := item["id"]; ok && value != nil {
				PrintText(fmt.Sprint(value))
			}
		}
		return
	}
	if len(items) == 0 {
		PrintErr("No " + label + " found.")
		return
	}
	PrintText(RenderTable(columns, items))
	if truncated {
		hint := ""
		if nextCursor != "" {
			hint = " Next: --cursor " + nextCursor
		}
		PrintErr("warning: stopped at the 10,000 item cap; results are truncated." + hint)
	} else if hasMore && nextCursor != "" {
		PrintErr(fmt.Sprintf("Showing %d. Next: --cursor %s", len(items), nextCursor))
	}
}

// EmitObject writes one resource or a handful of key/value lines.
func EmitObject(object map[string]any, ctx *Context, opts map[string]any, fields [][2]string) {
	switch ctx.Output {
	case "json":
		PrintJSON(object)
		return
	case "quiet":
		if value, ok := object["id"]; ok && value != nil {
			PrintText(fmt.Sprint(value))
		}
		return
	}
	for _, field := range fields {
		value := object[field[0]]
		switch typed := value.(type) {
		case nil:
			value = "-"
		case map[string]any, []any:
			body, _ := json.Marshal(typed)
			value = string(body)
		}
		PrintText(fmt.Sprintf("%s: %v", field[1], value))
	}
}

// EmitAction writes a result object or a one-line human confirmation.
func EmitAction(payload map[string]any, ctx *Context, message string) {
	if ctx.Output == "json" {
		PrintJSON(payload)
		return
	}
	PrintText(message)
}

// EmitDryRun prints the structured request and the resolved target.
func EmitDryRun(preview map[string]any, ctx *Context, opts map[string]any) {
	if target := targetDict(ctx); target != nil {
		preview["target"] = target
	}
	if ctx.Output == "json" {
		PrintJSON(preview)
		return
	}
	PrintErr("Dry run: no request sent")
	PrintErr(fmt.Sprintf("%v %v", preview["method"], preview["url"]))
	if headers, ok := preview["headers"]; ok {
		body, _ := json.Marshal(headers)
		PrintErr("headers: " + string(body))
	}
	if body, ok := preview["body"]; ok && body != nil {
		encoded, _ := json.Marshal(body)
		PrintErr("body: " + string(encoded))
	}
	if target := targetDict(ctx); target != nil {
		PrintErr(fmt.Sprintf("target: profile %s, %s, org %s, project %s, API %s",
			target["profile"], target["base_url"], target["org"], target["project"], target["api_version"]))
	}
}

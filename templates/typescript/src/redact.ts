const SENSITIVE = ["token", "secret", "password", "key", "authorization", "cookie"];

export function mask(value: unknown): unknown {
  if (value === null || value === undefined || value === "") return value;
  const text = String(value);
  if (text.length < 20) return "****";
  return text.slice(0, 4) + "****" + text.slice(-4);
}

export function redactValue(key: string, value: unknown): unknown {
  const lower = key.toLowerCase();
  if (SENSITIVE.some((part) => lower.includes(part))) return mask(value);
  if (Array.isArray(value)) return value.map((item) => redactValue(key, item));
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [nestedKey, nestedValue] of Object.entries(value as Record<string, unknown>)) {
      out[nestedKey] = redactValue(nestedKey, nestedValue);
    }
    return out;
  }
  return value;
}

export function redactHeaders(headers: Record<string, string>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(headers)) out[key] = redactValue(key, value);
  return out;
}

export function redactText(text: string, secrets: Array<string | null | undefined>): string {
  let out = String(text ?? "");
  for (const secret of secrets) {
    if (secret) out = out.split(secret).join(String(mask(secret)));
  }
  return out;
}

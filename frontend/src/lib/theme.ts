export const DEFAULT_ACCENT_COLOR = "#4f8cff";
export const ACCENT_STORAGE_KEY = "minebridge.accentColor";

export function normalizeHexColor(value: string): string | null {
  const trimmed = value.trim();
  const short = /^#([0-9a-f]{3})$/i.exec(trimmed);
  if (short) {
    return `#${short[1]
      .split("")
      .map((char) => char + char)
      .join("")}`.toLowerCase();
  }

  if (/^#[0-9a-f]{6}$/i.test(trimmed)) return trimmed.toLowerCase();
  return null;
}

export function hexToRgbTriplet(hex: string): string {
  const normalized = normalizeHexColor(hex) ?? DEFAULT_ACCENT_COLOR;
  const value = normalized.slice(1);
  const r = Number.parseInt(value.slice(0, 2), 16);
  const g = Number.parseInt(value.slice(2, 4), 16);
  const b = Number.parseInt(value.slice(4, 6), 16);
  return `${r} ${g} ${b}`;
}

export function readStoredAccentColor(): string {
  if (typeof window === "undefined") return DEFAULT_ACCENT_COLOR;
  const stored = window.localStorage.getItem(ACCENT_STORAGE_KEY);
  return normalizeHexColor(stored ?? "") ?? DEFAULT_ACCENT_COLOR;
}

export function applyAccentColor(hex: string): void {
  const normalized = normalizeHexColor(hex) ?? DEFAULT_ACCENT_COLOR;
  document.documentElement.style.setProperty("--accent", normalized);
  document.documentElement.style.setProperty("--accent-rgb", hexToRgbTriplet(normalized));
}

export function readCssVariable(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const value = window.getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

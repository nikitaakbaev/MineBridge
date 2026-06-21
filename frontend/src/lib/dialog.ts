type DialogFilter = { name: string; extensions: string[] };

export const isElectronEnvironment = (): boolean =>
  typeof window !== "undefined" && Boolean(window.minebridge?.pickDirectory);

export async function pickDirectory(options: {
  title?: string;
  defaultPath?: string;
} = {}): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const bridge = window.minebridge;
  if (bridge?.pickDirectory) {
    return bridge.pickDirectory(options);
  }
  const result = window.prompt(options.title || "Введите путь к папке", options.defaultPath || "");
  return result?.trim() ? result.trim() : null;
}

export async function pickFile(options: {
  title?: string;
  defaultPath?: string;
  filters?: DialogFilter[];
} = {}): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const bridge = window.minebridge;
  if (bridge?.pickFile) {
    return bridge.pickFile(options);
  }
  const result = window.prompt(options.title || "Введите путь к файлу", options.defaultPath || "");
  return result?.trim() ? result.trim() : null;
}

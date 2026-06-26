/// <reference types="vite/client" />

type DialogFilter = { name: string; extensions: string[] };

interface MinebridgeBridge {
  platform: string;
  versions: Record<string, string>;
  apiToken?: string;
  pickDirectory?: (options?: {
    title?: string;
    defaultPath?: string;
  }) => Promise<string | null>;
  pickFile?: (options?: {
    title?: string;
    defaultPath?: string;
    filters?: DialogFilter[];
  }) => Promise<string | null>;
}

interface Window {
  minebridge?: MinebridgeBridge;
}

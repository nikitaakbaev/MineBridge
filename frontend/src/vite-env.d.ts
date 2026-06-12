/// <reference types="vite/client" />

interface Window {
  minebridge?: {
    platform: string;
    versions: Record<string, string>;
  };
}

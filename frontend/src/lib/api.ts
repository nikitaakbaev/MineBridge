import type {
  ApiMessage,
  CommandOutput,
  DiagnosticResult,
  MinecraftConfig,
  Profile,
  ProfileBundle,
  SectionProfileBundle,
  TunnelConfig,
  VpsConfig
} from "./types";

export const API_BASE = "http://127.0.0.1:47831";
export const WS_URL = "ws://127.0.0.1:47831/ws/events";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers
    },
    ...options
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail || detail;
    } catch {
      detail = await response.text();
    }
    throw new Error(detail || `HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}

export const api = {
  health: () => request<ApiMessage>("/api/health"),
  activeProfile: () => request<ProfileBundle>("/api/profiles/active"),

  vpsProfiles: () => request<Profile[]>("/api/profiles/vps"),
  activeVpsProfile: () => request<SectionProfileBundle<VpsConfig>>("/api/profiles/vps/active"),
  saveVpsProfile: (id: number, config: VpsConfig) =>
    request<SectionProfileBundle<VpsConfig>>(`/api/profiles/vps/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ config })
    }),
  createVpsProfile: (name: string) =>
    request<SectionProfileBundle<VpsConfig>>("/api/profiles/vps", {
      method: "POST",
      body: JSON.stringify({ name })
    }),
  setActiveVpsProfile: (id: number) =>
    request<SectionProfileBundle<VpsConfig>>(`/api/profiles/vps/${id}/active`, {
      method: "POST"
    }),

  minecraftProfiles: () => request<Profile[]>("/api/profiles/minecraft"),
  activeMinecraftProfile: () =>
    request<SectionProfileBundle<MinecraftConfig>>("/api/profiles/minecraft/active"),
  saveMinecraftProfile: (id: number, config: MinecraftConfig) =>
    request<SectionProfileBundle<MinecraftConfig>>(`/api/profiles/minecraft/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ config })
    }),
  createMinecraftProfile: (name: string) =>
    request<SectionProfileBundle<MinecraftConfig>>("/api/profiles/minecraft", {
      method: "POST",
      body: JSON.stringify({ name })
    }),
  setActiveMinecraftProfile: (id: number) =>
    request<SectionProfileBundle<MinecraftConfig>>(`/api/profiles/minecraft/${id}/active`, {
      method: "POST"
    }),

  tunnelProfiles: () => request<Profile[]>("/api/profiles/tunnels"),
  activeTunnelProfile: () =>
    request<SectionProfileBundle<TunnelConfig>>("/api/profiles/tunnels/active"),
  saveTunnelProfile: (id: number, config: TunnelConfig) =>
    request<SectionProfileBundle<TunnelConfig>>(`/api/profiles/tunnels/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ config })
    }),
  createTunnelProfile: (name: string) =>
    request<SectionProfileBundle<TunnelConfig>>("/api/profiles/tunnels", {
      method: "POST",
      body: JSON.stringify({ name })
    }),
  setActiveTunnelProfile: (id: number) =>
    request<SectionProfileBundle<TunnelConfig>>(`/api/profiles/tunnels/${id}/active`, {
      method: "POST"
    }),

  checkSsh: (password = "") =>
    request<CommandOutput>("/api/vps/check-ssh", {
      method: "POST",
      body: JSON.stringify({ password })
    }),
  installFrps: (password = "") =>
    request<ApiMessage>("/api/vps/install-frps", {
      method: "POST",
      body: JSON.stringify({ password })
    }),
  frpsStatus: (password = "") =>
    request<CommandOutput>("/api/vps/frps/status", {
      method: "POST",
      body: JSON.stringify({ password })
    }),
  startFrps: (password = "") =>
    request<CommandOutput>("/api/vps/frps/start", {
      method: "POST",
      body: JSON.stringify({ password })
    }),
  stopFrps: (password = "") =>
    request<CommandOutput>("/api/vps/frps/stop", {
      method: "POST",
      body: JSON.stringify({ password })
    }),

  saveServerProperties: () =>
    request<ApiMessage>("/api/minecraft/server-properties", { method: "POST" }),
  startMinecraft: () => request<ApiMessage>("/api/minecraft/start", { method: "POST" }),
  stopMinecraft: () => request<ApiMessage>("/api/minecraft/stop", { method: "POST" }),
  restartMinecraft: () => request<ApiMessage>("/api/minecraft/restart", { method: "POST" }),
  sendMinecraftCommand: (command: string) =>
    request<ApiMessage>("/api/minecraft/command", {
      method: "POST",
      body: JSON.stringify({ command })
    }),

  createFrpcConfig: () => request<ApiMessage>("/api/frpc/config", { method: "POST" }),
  downloadFrpc: () => request<ApiMessage>("/api/frpc/download", { method: "POST" }),
  startFrpc: () => request<ApiMessage>("/api/frpc/start", { method: "POST" }),
  stopFrpc: () => request<ApiMessage>("/api/frpc/stop", { method: "POST" }),
  checkFrpcPort: () => request<ApiMessage>("/api/frpc/check-port", { method: "POST" }),

  diagnostics: () =>
    request<DiagnosticResult[]>("/api/diagnostics/run", {
      method: "POST"
    }),
  appLog: () => request<ApiMessage>("/api/logs/app")
};

export type DiagnosticStatus = "OK" | "WARNING" | "ERROR";

export type Profile = {
  id: number | null;
  name: string;
  created_at?: string | null;
  updated_at?: string | null;
  is_default: boolean;
};

export type VpsConfig = {
  id?: number | null;
  profile_id?: number | null;
  host: string;
  ssh_port: number;
  username: string;
  auth_type: "password" | "private_key";
  password_encrypted?: string | null;
  private_key_path: string;
  install_dir: string;
  frps_bind_port: number;
  dashboard_enabled: boolean;
  dashboard_port: number;
};

export type MinecraftConfig = {
  id?: number | null;
  profile_id?: number | null;
  server_dir: string;
  jar_path: string;
  java_path: string;
  xms: string;
  xmx: string;
  mc_port: number;
  server_type: "Vanilla" | "Paper" | "Fabric" | "Forge" | "NeoForge";
  mc_version: string;
  online_mode: boolean;
  difficulty: "peaceful" | "easy" | "normal" | "hard";
  max_players: number;
  motd: string;
  view_distance: number;
  simulation_distance: number;
};

export type TunnelConfig = {
  id?: number | null;
  profile_id?: number | null;
  local_ip: string;
  local_port: number;
  remote_port: number;
  protocol: "tcp";
  frp_server_addr: string;
  frp_server_bind_port: number;
  frp_token: string;
  auto_start_frpc: boolean;
};

export type ProfileBundle = {
  profile: Profile;
  vps: VpsConfig;
  minecraft: MinecraftConfig;
  tunnel: TunnelConfig;
};

export type SectionProfileBundle<TConfig> = {
  profile: Profile;
  config: TConfig;
};

export type DiagnosticResult = {
  status: DiagnosticStatus;
  name: string;
  description: string;
  fix_available: boolean;
  fix_id?: string | null;
};

export type ApiMessage = {
  message: string;
};

export type CommandOutput = {
  stdout: string;
  stderr: string;
  exit_status: number | null;
};

export type BackendEvent = {
  type: string;
  payload: Record<string, unknown>;
};

export type ScreenId =
  | "dashboard"
  | "servers"
  | "minecraft"
  | "tunnels"
  | "vps"
  | "diagnostics"
  | "logs"
  | "settings";

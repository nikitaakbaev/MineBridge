import { create } from "zustand";

import type { BackendEvent, MetricsSample, RuntimeState, ScreenId } from "../lib/types";

type RuntimeStatus = "idle" | "running" | "stopping" | "stopped" | "error" | string;

const METRICS_LIMIT = 90;
const LOG_LIMIT = 500;

type AppState = {
  activeScreen: ScreenId;
  minecraftStatus: RuntimeStatus;
  frpcStatus: RuntimeStatus;
  backendConnected: boolean;
  minecraftLogs: string[];
  frpcLogs: string[];
  vpsLogs: string[];
  metrics: MetricsSample[];
  latest: MetricsSample | null;
  players: string[];
  playerCount: number;
  uptimeSeconds: number;
  serverReadyAt: number | null;
  serverStartedAt: number | null;
  setActiveScreen: (screen: ScreenId) => void;
  setBackendConnected: (connected: boolean) => void;
  pushLog: (target: "minecraft" | "frpc" | "vps", line: string) => void;
  hydrateState: (state: RuntimeState) => void;
  ingestEvent: (event: BackendEvent) => void;
};

const limit = (items: string[]) => items.slice(-LOG_LIMIT);
const limitMetrics = (items: MetricsSample[]) => items.slice(-METRICS_LIMIT);

export const useAppStore = create<AppState>((set) => ({
  activeScreen: "dashboard",
  minecraftStatus: "idle",
  frpcStatus: "idle",
  backendConnected: false,
  minecraftLogs: [],
  frpcLogs: [],
  vpsLogs: [],
  metrics: [],
  latest: null,
  players: [],
  playerCount: 0,
  uptimeSeconds: 0,
  serverReadyAt: null,
  serverStartedAt: null,
  setActiveScreen: (activeScreen) => set({ activeScreen }),
  setBackendConnected: (backendConnected) => set({ backendConnected }),
  pushLog: (target, line) =>
    set((state) => {
      if (target === "minecraft") {
        return { minecraftLogs: limit([...state.minecraftLogs, line]) };
      }
      if (target === "frpc") {
        return { frpcLogs: limit([...state.frpcLogs, line]) };
      }
      return { vpsLogs: limit([...state.vpsLogs, line]) };
    }),
  hydrateState: (state) =>
    set(() => {
      const running = state.minecraft_status === "running";
      return {
        minecraftStatus: (state.minecraft_status as RuntimeStatus) ?? "idle",
        frpcStatus: (state.frpc_status as RuntimeStatus) ?? "idle",
        players: state.players ?? [],
        playerCount: state.player_count ?? 0,
        uptimeSeconds: state.uptime_seconds ?? 0,
        serverStartedAt: running ? Date.now() - (state.uptime_seconds ?? 0) * 1000 : null,
        metrics: state.metrics ? [state.metrics] : [],
        latest: state.metrics ?? null
      };
    }),
  ingestEvent: (event) =>
    set((state) => {
      switch (event.type) {
        case "minecraft.log":
          return { minecraftLogs: limit([...state.minecraftLogs, String(event.payload.line ?? "")]) };
        case "frpc.log":
          return { frpcLogs: limit([...state.frpcLogs, String(event.payload.line ?? "")]) };
        case "minecraft.status": {
          const status = String(event.payload.status ?? "idle") as RuntimeStatus;
          const serverStartedAt =
            status === "running"
              ? state.serverStartedAt ?? Date.now()
              : status === "stopped" || status === "idle" || status === "error"
                ? null
                : state.serverStartedAt;
          return { minecraftStatus: status, serverStartedAt };
        }
        case "frpc.status":
          return { frpcStatus: String(event.payload.status ?? "idle") as RuntimeStatus };
        case "minecraft.ready":
          return { serverReadyAt: Date.now() };
        case "minecraft.error":
          return {
            minecraftLogs: limit([
              ...state.minecraftLogs,
              `\u001b[31m[error] ${String(event.payload.message ?? "")}\u001b[0m`
            ])
          };
        case "minecraft.players":
          return {
            players: (event.payload.players as string[]) ?? [],
            playerCount: Number(event.payload.count ?? 0)
          };
        case "metrics.sample": {
          const sample = event.payload as unknown as MetricsSample;
          return {
            metrics: limitMetrics([...state.metrics, sample]),
            latest: sample,
            playerCount: sample.players ?? state.playerCount
          };
        }
        case "vps.action":
          return {
            vpsLogs: limit([
              ...state.vpsLogs,
              `${String(event.payload.action ?? "vps")}: ${String(event.payload.status ?? "")}`
            ])
          };
        default:
          return state;
      }
    })
}));

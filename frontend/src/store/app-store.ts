import { create } from "zustand";

import type { BackendEvent, ScreenId } from "../lib/types";

type RuntimeStatus = "idle" | "running" | "stopping" | "stopped" | "error";

type AppState = {
  activeScreen: ScreenId;
  minecraftStatus: RuntimeStatus;
  frpcStatus: RuntimeStatus;
  backendConnected: boolean;
  minecraftLogs: string[];
  frpcLogs: string[];
  vpsLogs: string[];
  setActiveScreen: (screen: ScreenId) => void;
  setBackendConnected: (connected: boolean) => void;
  pushLog: (target: "minecraft" | "frpc" | "vps", line: string) => void;
  ingestEvent: (event: BackendEvent) => void;
};

const limit = (items: string[]) => items.slice(-500);

export const useAppStore = create<AppState>((set) => ({
  activeScreen: "dashboard",
  minecraftStatus: "idle",
  frpcStatus: "idle",
  backendConnected: false,
  minecraftLogs: [],
  frpcLogs: [],
  vpsLogs: [],
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
  ingestEvent: (event) =>
    set((state) => {
      if (event.type === "minecraft.log") {
        return { minecraftLogs: limit([...state.minecraftLogs, String(event.payload.line ?? "")]) };
      }
      if (event.type === "frpc.log") {
        return { frpcLogs: limit([...state.frpcLogs, String(event.payload.line ?? "")]) };
      }
      if (event.type === "minecraft.status") {
        return { minecraftStatus: String(event.payload.status ?? "idle") as RuntimeStatus };
      }
      if (event.type === "frpc.status") {
        return { frpcStatus: String(event.payload.status ?? "idle") as RuntimeStatus };
      }
      if (event.type === "vps.action") {
        return {
          vpsLogs: limit([
            ...state.vpsLogs,
            `${String(event.payload.action ?? "vps")}: ${String(event.payload.status ?? "")}`
          ])
        };
      }
      return state;
    })
}));

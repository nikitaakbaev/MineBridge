import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";

import { AppShell } from "./components/layout/AppShell";
import { ConsoleDrawer } from "./components/ui/ConsoleDrawer";
import { useBackendEvents } from "./hooks/useBackendEvents";
import { api } from "./lib/api";
import { applyAccentColor } from "./lib/theme";
import { useAppStore } from "./store/app-store";
import { HomeScreen } from "./screens/HomeScreen";
import { SetupScreen } from "./screens/SetupScreen";
import { LogsScreen } from "./screens/LogsScreen";
import { SettingsScreen } from "./screens/SettingsScreen";

const screens = {
  home: <HomeScreen />,
  setup: <SetupScreen />,
  logs: <LogsScreen />,
  settings: <SettingsScreen />
};

export function App() {
  useBackendEvents();
  const activeScreen = useAppStore((state) => state.activeScreen);
  const setupStatus = useAppStore((state) => state.setupStatus);
  const setSetupStatus = useAppStore((state) => state.setSetupStatus);
  const setActiveScreen = useAppStore((state) => state.setActiveScreen);
  const toggleConsole = useAppStore((state) => state.toggleConsole);
  const accentColor = useAppStore((state) => state.accentColor);

  const setupQuery = useQuery({
    queryKey: ["setup-status"],
    queryFn: api.getSetupStatus,
    staleTime: 5_000
  });

  useEffect(() => {
    if (!setupQuery.data) return;
    setSetupStatus(setupQuery.data);
  }, [setupQuery.data, setSetupStatus]);

  // First-load redirect: only when we don't yet know setup state at all.
  useEffect(() => {
    if (setupStatus !== null) return;
    if (!setupQuery.data) return;
    if (!setupQuery.data.completed) setActiveScreen("setup");
  }, [setupQuery.data, setupStatus, setActiveScreen]);

  useEffect(() => {
    applyAccentColor(accentColor);
  }, [accentColor]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "`" && !event.metaKey && !event.ctrlKey && !event.altKey) {
        const target = event.target as HTMLElement | null;
        if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) return;
        event.preventDefault();
        toggleConsole();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [toggleConsole]);

  return (
    <AppShell>
      <AnimatePresence mode="wait">
        <motion.div
          key={activeScreen}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.18 }}
          className="screen-motion"
        >
          {screens[activeScreen]}
        </motion.div>
      </AnimatePresence>
      <ConsoleDrawer />
    </AppShell>
  );
}

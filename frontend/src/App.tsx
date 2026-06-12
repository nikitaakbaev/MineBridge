import { AnimatePresence, motion } from "framer-motion";

import { AppShell } from "./components/layout/AppShell";
import { useBackendEvents } from "./hooks/useBackendEvents";
import { useAppStore } from "./store/app-store";
import { DashboardScreen } from "./screens/DashboardScreen";
import { ServersScreen } from "./screens/ServersScreen";
import { MinecraftScreen } from "./screens/MinecraftScreen";
import { TunnelsScreen } from "./screens/TunnelsScreen";
import { VpsScreen } from "./screens/VpsScreen";
import { DiagnosticsScreen } from "./screens/DiagnosticsScreen";
import { LogsScreen } from "./screens/LogsScreen";
import { SettingsScreen } from "./screens/SettingsScreen";

const screens = {
  dashboard: <DashboardScreen />,
  servers: <ServersScreen />,
  minecraft: <MinecraftScreen />,
  tunnels: <TunnelsScreen />,
  vps: <VpsScreen />,
  diagnostics: <DiagnosticsScreen />,
  logs: <LogsScreen />,
  settings: <SettingsScreen />
};

export function App() {
  useBackendEvents();
  const activeScreen = useAppStore((state) => state.activeScreen);

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
    </AppShell>
  );
}

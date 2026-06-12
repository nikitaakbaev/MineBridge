import {
  Activity,
  Boxes,
  Gauge,
  Home,
  ListChecks,
  Monitor,
  ScrollText,
  Server,
  Settings,
  Waypoints
} from "lucide-react";

import type { ScreenId } from "../../lib/types";
import { useAppStore } from "../../store/app-store";

const items: Array<{ id: ScreenId; label: string; icon: typeof Home }> = [
  { id: "dashboard", label: "Dashboard", icon: Home },
  { id: "servers", label: "Servers", icon: Boxes },
  { id: "minecraft", label: "Minecraft", icon: Monitor },
  { id: "tunnels", label: "Tunnels", icon: Waypoints },
  { id: "vps", label: "VPS", icon: Server },
  { id: "diagnostics", label: "Diagnostics", icon: ListChecks },
  { id: "logs", label: "Logs", icon: ScrollText },
  { id: "settings", label: "Settings", icon: Settings }
];

export function Sidebar() {
  const activeScreen = useAppStore((state) => state.activeScreen);
  const setActiveScreen = useAppStore((state) => state.setActiveScreen);
  const connected = useAppStore((state) => state.backendConnected);

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <Gauge size={22} />
        </div>
        <div>
          <strong>MineBridge</strong>
          <span>FRP Launcher</span>
        </div>
      </div>

      <nav className="nav-list">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              className={activeScreen === item.id ? "nav-item active" : "nav-item"}
              onClick={() => setActiveScreen(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-status">
        <Activity size={16} />
        <div>
          <strong>{connected ? "Backend online" : "Backend starting"}</strong>
          <span>127.0.0.1:47831</span>
        </div>
      </div>
    </aside>
  );
}

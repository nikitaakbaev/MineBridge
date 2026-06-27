import { Activity, Gauge, Home, ScrollText, Settings, Wand2 } from "lucide-react";

import type { ScreenId } from "../../lib/types";
import { useAppStore } from "../../store/app-store";

const items: Array<{ id: ScreenId; label: string; icon: typeof Home }> = [
  { id: "home", label: "Home", icon: Home },
  { id: "setup", label: "Настройка", icon: Wand2 },
  { id: "logs", label: "Логи", icon: ScrollText },
  { id: "settings", label: "Настройки", icon: Settings }
];

export function Sidebar() {
  const activeScreen = useAppStore((state) => state.activeScreen);
  const setActiveScreen = useAppStore((state) => state.setActiveScreen);
  const connected = useAppStore((state) => state.backendConnected);
  const setupStatus = useAppStore((state) => state.setupStatus);

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <Gauge size={22} />
        </div>
        <div>
          <strong>MineBridge</strong>
          <span>FRP Control</span>
        </div>
      </div>

      <nav className="nav-list" aria-label="Main navigation">
        {items.map((item) => {
          const Icon = item.icon;
          const showSetupHint = item.id === "setup" && setupStatus && !setupStatus.completed;
          return (
            <button
              key={item.id}
              className={activeScreen === item.id ? "nav-item active" : "nav-item"}
              onClick={() => setActiveScreen(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
              {showSetupHint && <em className="nav-dot" aria-label="требуется настройка" />}
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

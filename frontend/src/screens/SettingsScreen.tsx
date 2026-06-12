import { Cpu, Database, MonitorCog } from "lucide-react";

import { Card } from "../components/ui/Card";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { StatusBadge } from "../components/ui/StatusBadge";

export function SettingsScreen() {
  const platform = window.minebridge?.platform || "browser";

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Settings"
        title="Настройки приложения"
        description="Пока это обзор окружения Electron. Управление настройками будет расширяться после замены Qt UI."
      />

      <div className="card-grid">
        <Card title="Electron shell" className="feature-card">
          <MonitorCog size={32} />
          <h3>{platform}</h3>
          <p>Single-instance и запуск backend уже находятся в Electron main process.</p>
          <StatusBadge status="OK" />
        </Card>
        <Card title="Python backend" className="feature-card">
          <Cpu size={32} />
          <h3>FastAPI</h3>
          <p>Локальный API слушает 127.0.0.1:47831 и владеет бизнес-логикой.</p>
          <StatusBadge status="OK" />
        </Card>
        <Card title="Storage" className="feature-card">
          <Database size={32} />
          <h3>SQLite + profiles</h3>
          <p>Профили остаются в существующем Python repository layer.</p>
          <StatusBadge status="OK" />
        </Card>
      </div>
    </div>
  );
}

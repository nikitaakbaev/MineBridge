import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ListChecks, RefreshCcw, ScrollText } from "lucide-react";

import { api } from "../lib/api";
import type { DiagnosticResult } from "../lib/types";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { SelectInput } from "../components/ui/Field";
import { StatusBadge } from "../components/ui/StatusBadge";
import { TerminalConsole } from "../components/ui/TerminalConsole";
import { useAppStore } from "../store/app-store";

type Source = "minecraft" | "frpc" | "vps" | "app";

const SOURCE_LABEL: Record<Source, string> = {
  minecraft: "Minecraft сервер",
  frpc: "FRP туннель",
  vps: "VPS-операции",
  app: "MineBridge backend"
};

export function LogsScreen() {
  const [source, setSource] = useState<Source>("minecraft");
  const minecraftLogs = useAppStore((state) => state.minecraftLogs);
  const frpcLogs = useAppStore((state) => state.frpcLogs);
  const vpsLogs = useAppStore((state) => state.vpsLogs);
  const [diagnostics, setDiagnostics] = useState<DiagnosticResult[] | null>(null);

  const appLog = useQuery({ queryKey: ["app-log"], queryFn: api.appLog });
  const refreshAppLog = useMutation({
    mutationFn: async () => appLog.refetch()
  });

  const runDiagnostics = useMutation({
    mutationFn: api.diagnostics,
    onSuccess: (results) => setDiagnostics(results)
  });

  useEffect(() => {
    runDiagnostics.mutate();
    const id = window.setInterval(() => runDiagnostics.mutate(), 30_000);
    return () => window.clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const lines = (() => {
    switch (source) {
      case "minecraft":
        return minecraftLogs;
      case "frpc":
        return frpcLogs;
      case "vps":
        return vpsLogs;
      case "app":
        return (appLog.data?.message || "")
          .split(/\r?\n/)
          .filter((line) => line.length > 0);
    }
  })();

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Logs & diagnostics"
        title="Логи и диагностика"
        description="Один экран для всех логов и автоматических проверок."
        action={
          <div className="hero-actions">
            <SelectInput value={source} onChange={(e) => setSource(e.target.value as Source)}>
              {(Object.keys(SOURCE_LABEL) as Source[]).map((key) => (
                <option key={key} value={key}>
                  {SOURCE_LABEL[key]}
                </option>
              ))}
            </SelectInput>
            {source === "app" && (
              <Button
                icon={<RefreshCcw size={14} />}
                onClick={() => refreshAppLog.mutate()}
                disabled={refreshAppLog.isPending}
              >
                Обновить
              </Button>
            )}
          </div>
        }
      />

      <Card title={SOURCE_LABEL[source]} eyebrow="Stream" action={<ScrollText size={14} />}>
        <TerminalConsole title={SOURCE_LABEL[source]} lines={lines.slice(-1500)} />
      </Card>

      <Card
        title="Диагностика"
        eyebrow="Auto"
        action={
          <Button
            icon={<ListChecks size={14} />}
            onClick={() => runDiagnostics.mutate()}
            disabled={runDiagnostics.isPending}
          >
            Запустить заново
          </Button>
        }
      >
        {diagnostics === null ? (
          <p className="muted">Запуск диагностики...</p>
        ) : diagnostics.length === 0 ? (
          <p className="muted">Нет результатов.</p>
        ) : (
          <div className="diagnostics-card">
            {diagnostics.map((row) => (
              <div className="diagnostics-row" key={`${row.name}-${row.description}`}>
                <StatusBadge status={row.status} label={row.status} />
                <strong>{row.name}</strong>
                <span className="muted">{row.description}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

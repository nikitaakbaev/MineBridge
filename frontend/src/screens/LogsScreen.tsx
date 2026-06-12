import { useMutation, useQuery } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";

import { api } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { TerminalConsole } from "../components/ui/TerminalConsole";
import { useAppStore } from "../store/app-store";

export function LogsScreen() {
  const appLog = useQuery({ queryKey: ["app-log"], queryFn: api.appLog });
  const minecraftLogs = useAppStore((state) => state.minecraftLogs);
  const frpcLogs = useAppStore((state) => state.frpcLogs);
  const refresh = useMutation({
    mutationFn: async () => appLog.refetch()
  });

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Runtime logs"
        title="Консоли и события"
        description="xterm.js выводит логи backend, Minecraft и frpc в отдельных живых панелях."
        action={
          <Button icon={<RefreshCw size={16} />} onClick={() => refresh.mutate()}>
            Обновить app log
          </Button>
        }
      />

      <div className="log-grid">
        <TerminalConsole
          title="App logs"
          lines={(appLog.data?.message || "").split("\n")}
        />
        <TerminalConsole title="Minecraft logs" lines={minecraftLogs} />
        <TerminalConsole title="frpc logs" lines={frpcLogs} />
      </div>
    </div>
  );
}

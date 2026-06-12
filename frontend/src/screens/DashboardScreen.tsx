import { useMutation, useQuery } from "@tanstack/react-query";
import { Play, Power, RefreshCw, Share2 } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import { TerminalConsole } from "../components/ui/TerminalConsole";
import { useAppStore } from "../store/app-store";

const sampleResources = [
  { name: "00:00", cpu: 18, ram: 32 },
  { name: "00:05", cpu: 24, ram: 35 },
  { name: "00:10", cpu: 20, ram: 41 },
  { name: "00:15", cpu: 34, ram: 45 },
  { name: "00:20", cpu: 28, ram: 38 },
  { name: "00:25", cpu: 42, ram: 49 }
];

export function DashboardScreen() {
  const profile = useQuery({ queryKey: ["active-profile"], queryFn: api.activeProfile });
  const minecraftStatus = useAppStore((state) => state.minecraftStatus);
  const frpcStatus = useAppStore((state) => state.frpcStatus);
  const minecraftLogs = useAppStore((state) => state.minecraftLogs);
  const frpcLogs = useAppStore((state) => state.frpcLogs);

  const startAll = useMutation({
    mutationFn: async () => {
      await api.startMinecraft();
      await api.startFrpc();
    }
  });
  const stopAll = useMutation({
    mutationFn: async () => {
      await api.stopFrpc();
      await api.stopMinecraft();
    }
  });

  const connectAddress = profile.data?.vps.host
    ? `${profile.data.vps.host}:${profile.data.tunnel.remote_port}`
    : "VPS не выбран";

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Home server launcher"
        title="Открыть Minecraft-сервер друзьям"
        description="Dashboard скрывает внутреннюю сложность FRP и показывает только то, что важно для запуска."
        action={
          <div className="hero-actions">
            <Button
              variant="primary"
              icon={<Play size={18} />}
              disabled={startAll.isPending}
              onClick={() => startAll.mutate()}
            >
              Запустить сервер
            </Button>
            <Button icon={<Power size={18} />} disabled={stopAll.isPending} onClick={() => stopAll.mutate()}>
              Остановить
            </Button>
          </div>
        }
      />

      <section className="dashboard-hero">
        <div>
          <p className="eyebrow">Адрес для друзей</p>
          <h2>{connectAddress}</h2>
          <p>{profile.data?.minecraft.motd || "Настройте Minecraft-профиль и VPS."}</p>
        </div>
        <Share2 size={42} />
      </section>

      <div className="status-grid">
        <Card title="Minecraft">
          <StatusBadge status={minecraftStatus} label={minecraftStatus} />
          <p className="muted">Локальный Java server</p>
        </Card>
        <Card title="FRP">
          <StatusBadge status={frpcStatus} label={frpcStatus} />
          <p className="muted">Туннель наружу через VPS</p>
        </Card>
        <Card title="VPS">
          <StatusBadge status={profile.data?.vps.host ? "OK" : "WARNING"} />
          <p className="muted">{profile.data?.vps.host || "Адрес VPS не задан"}</p>
        </Card>
        <Card title="Профили">
          <StatusBadge status="OK" label={profile.data?.profile.name || "default"} />
          <p className="muted">Активная сборка настроек</p>
        </Card>
      </div>

      <div className="two-columns">
        <Card title="Ресурсы" action={<RefreshCw size={16} />}>
          <div className="chart">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={sampleResources}>
                <XAxis dataKey="name" stroke="#7d8da7" />
                <YAxis stroke="#7d8da7" />
                <Tooltip />
                <Area type="monotone" dataKey="cpu" stroke="#60a5fa" fill="#2563eb55" />
                <Area type="monotone" dataKey="ram" stroke="#34d399" fill="#10b98144" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <TerminalConsole title="Живой вывод" lines={[...minecraftLogs, ...frpcLogs].slice(-80)} />
      </div>
    </div>
  );
}

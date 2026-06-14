import { useMutation, useQuery } from "@tanstack/react-query";
import { Activity, Cpu, Gauge as GaugeIcon, MemoryStick, Network, Play, Power, Share2, Users } from "lucide-react";

import { api } from "../lib/api";
import { formatDuration, formatMb, useUptime } from "../lib/format";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Gauge, MetricArea } from "../components/ui/charts";
import { Console } from "../components/ui/Console";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { StatTile } from "../components/ui/StatTile";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useAppStore } from "../store/app-store";

export function DashboardScreen() {
  const profile = useQuery({ queryKey: ["active-profile"], queryFn: api.activeProfile });
  const minecraftStatus = useAppStore((state) => state.minecraftStatus);
  const frpcStatus = useAppStore((state) => state.frpcStatus);
  const minecraftLogs = useAppStore((state) => state.minecraftLogs);
  const frpcLogs = useAppStore((state) => state.frpcLogs);
  const metrics = useAppStore((state) => state.metrics);
  const latest = useAppStore((state) => state.latest);
  const playerCount = useAppStore((state) => state.playerCount);
  const serverStartedAt = useAppStore((state) => state.serverStartedAt);
  const uptime = useUptime(serverStartedAt);

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

  const send = useMutation({ mutationFn: (command: string) => api.sendMinecraftCommand(command) });

  const connectAddress = profile.data?.vps.host
    ? `${profile.data.vps.host}:${profile.data.tunnel.remote_port}`
    : "VPS не выбран";

  const maxPlayers = profile.data?.minecraft.max_players ?? 20;
  const serverRunning = minecraftStatus === "running";

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Home server launcher"
        title="Открыть Minecraft-сервер друзьям"
        description="Живой мониторинг ресурсов, игроков и туннеля — всё в одном месте."
        action={
          <div className="hero-actions">
            <Button
              variant="primary"
              icon={<Play size={18} />}
              disabled={startAll.isPending}
              onClick={() => startAll.mutate()}
            >
              Запустить всё
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
          <div className="hero-pills">
            <span className="hero-pill">
              <Activity size={14} /> Minecraft: {minecraftStatus}
            </span>
            <span className="hero-pill">
              <Network size={14} /> FRP: {frpcStatus}
            </span>
            <span className="hero-pill">
              <Users size={14} /> {playerCount}/{maxPlayers} игроков
            </span>
            <span className="hero-pill">
              <GaugeIcon size={14} /> Аптайм: {serverRunning ? formatDuration(uptime) : "—"}
            </span>
          </div>
        </div>
        <Share2 size={42} />
      </section>

      <div className="stat-grid">
        <StatTile
          icon={<Cpu size={18} />}
          label="CPU системы"
          value={`${latest?.cpu ?? 0}%`}
          hint={`сервер: ${latest?.server_cpu ?? 0}%`}
          accent="#60a5fa"
          data={metrics}
          dataKey="cpu"
        />
        <StatTile
          icon={<MemoryStick size={18} />}
          label="RAM системы"
          value={`${latest?.ram_percent ?? 0}%`}
          hint={latest ? `${formatMb(latest.ram_used_mb)} / ${formatMb(latest.ram_total_mb)}` : "—"}
          accent="#34d399"
          data={metrics}
          dataKey="ram_percent"
        />
        <StatTile
          icon={<MemoryStick size={18} />}
          label="RAM сервера"
          value={latest ? formatMb(latest.server_ram_mb) : "0 МБ"}
          hint={serverRunning ? "java процесс" : "сервер остановлен"}
          accent="#f59e0b"
          data={metrics}
          dataKey="server_ram_mb"
        />
        <StatTile
          icon={<Network size={18} />}
          label="Сеть ↓ / ↑"
          value={`${latest?.net_down_kbps ?? 0} КБ/с`}
          hint={`↑ ${latest?.net_up_kbps ?? 0} КБ/с`}
          accent="#a78bfa"
          data={metrics}
          dataKey="net_down_kbps"
        />
      </div>

      <div className="two-columns">
        <Card title="Загрузка CPU" eyebrow="Live" action={<Cpu size={16} />}>
          <MetricArea
            data={metrics}
            domainMax={100}
            unit="%"
            series={[
              { key: "cpu", label: "Система", color: "#60a5fa" },
              { key: "server_cpu", label: "Сервер", color: "#f472b6" }
            ]}
          />
        </Card>
        <Card title="Игроки онлайн" eyebrow="Live" action={<Users size={16} />}>
          <MetricArea
            data={metrics}
            domainMax={Math.max(maxPlayers, 4)}
            series={[{ key: "players", label: "Игроки", color: "#34d399" }]}
          />
        </Card>
      </div>

      <div className="two-columns">
        <Card title="Память" eyebrow="Live" action={<MemoryStick size={16} />}>
          <MetricArea
            data={metrics}
            domainMax={100}
            unit="%"
            series={[{ key: "ram_percent", label: "Система %", color: "#34d399" }]}
          />
        </Card>
        <Card title="Сеть (КБ/с)" eyebrow="Live" action={<Network size={16} />}>
          <MetricArea
            data={metrics}
            series={[
              { key: "net_down_kbps", label: "Входящий", color: "#60a5fa" },
              { key: "net_up_kbps", label: "Исходящий", color: "#a78bfa" }
            ]}
          />
        </Card>
      </div>

      <div className="gauge-grid">
        <Card title="CPU сейчас">
          <Gauge value={latest?.cpu ?? 0} label="система" color="#60a5fa" />
        </Card>
        <Card title="RAM сейчас">
          <Gauge value={latest?.ram_percent ?? 0} label="память" color="#34d399" />
        </Card>
        <Card title="Игроки">
          <Gauge value={playerCount} max={Math.max(maxPlayers, 1)} label="онлайн" unit="" color="#f59e0b" />
        </Card>
        <Card title="Состояние">
          <div className="state-stack">
            <div className="state-row">
              <span>Minecraft</span>
              <StatusBadge status={minecraftStatus} label={minecraftStatus} />
            </div>
            <div className="state-row">
              <span>FRP туннель</span>
              <StatusBadge status={frpcStatus} label={frpcStatus} />
            </div>
            <div className="state-row">
              <span>VPS</span>
              <StatusBadge status={profile.data?.vps.host ? "OK" : "WARNING"} />
            </div>
          </div>
        </Card>
      </div>

      <Console
        title="Консоль сервера"
        lines={[...minecraftLogs, ...frpcLogs].slice(-160)}
        onSubmit={(command) => send.mutate(command)}
        disabled={!serverRunning}
        disabledHint="запустите сервер, чтобы вводить команды"
      />
    </div>
  );
}

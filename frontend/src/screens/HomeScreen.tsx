import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  Copy,
  Cpu,
  Gauge as GaugeIcon,
  MemoryStick,
  Network,
  Play,
  Power,
  RotateCcw,
  Square,
  Terminal,
  Users,
  Wand2
} from "lucide-react";

import { api } from "../lib/api";
import { formatDuration, formatMb, useUptime } from "../lib/format";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { OverflowMenu } from "../components/ui/OverflowMenu";
import { useAppStore } from "../store/app-store";

export function HomeScreen() {
  const queryClient = useQueryClient();
  const profile = useQuery({ queryKey: ["active-profile"], queryFn: api.activeProfile });
  const minecraftStatus = useAppStore((state) => state.minecraftStatus);
  const frpcStatus = useAppStore((state) => state.frpcStatus);
  const latest = useAppStore((state) => state.latest);
  const playerCount = useAppStore((state) => state.playerCount);
  const players = useAppStore((state) => state.players);
  const serverStartedAt = useAppStore((state) => state.serverStartedAt);
  const setupStatus = useAppStore((state) => state.setupStatus);
  const setActiveScreen = useAppStore((state) => state.setActiveScreen);
  const setConsoleOpen = useAppStore((state) => state.setConsoleOpen);
  const uptime = useUptime(serverStartedAt);

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const note = (message: string) => {
    setActionMessage(message);
    setActionError(null);
  };
  const fail = (err: unknown) => {
    setActionError(err instanceof Error ? err.message : String(err));
    setActionMessage(null);
  };

  const startAll = useMutation({
    mutationFn: async () => {
      await api.startMinecraft();
      await api.startFrpc();
    },
    onSuccess: () => note("Запуск отправлен."),
    onError: fail
  });
  const stopAll = useMutation({
    mutationFn: async () => {
      await api.stopFrpc();
      await api.stopMinecraft();
    },
    onSuccess: () => note("Остановка отправлена."),
    onError: fail
  });
  const restart = useMutation({
    mutationFn: async () => {
      await api.restartMinecraft();
    },
    onSuccess: () => note("Перезапуск Minecraft отправлен."),
    onError: fail
  });
  const writeProperties = useMutation({
    mutationFn: api.saveServerProperties,
    onSuccess: (r) => note(`server.properties: ${r.message}`),
    onError: fail
  });
  const writeEula = useMutation({
    mutationFn: api.createEulaFile,
    onSuccess: (r) => note(`eula.txt: ${r.message}`),
    onError: fail
  });

  const serverRunning = minecraftStatus === "running";
  const tunnelRunning = frpcStatus === "running";
  const setupIncomplete = setupStatus !== null && !setupStatus.completed;

  const connectAddress = profile.data?.vps.host
    ? `${profile.data.vps.host}:${profile.data.tunnel.remote_port}`
    : null;

  const onCopyAddress = async () => {
    if (!connectAddress) return;
    try {
      await navigator.clipboard.writeText(connectAddress);
      note("Адрес скопирован.");
    } catch (err) {
      fail(err);
    }
  };

  const ramTotalMb = latest?.ram_total_mb ?? 0;
  const ramUsedMb = latest?.ram_used_mb ?? 0;

  return (
    <div className="screen stack">
      {setupIncomplete && (
        <div className="home-banner" role="status">
          <div>
            <strong>Настройка не завершена.</strong>
            <span>Закончите мастер, чтобы открыть туннель друзьям.</span>
          </div>
          <Button
            icon={<Wand2 size={16} />}
            variant="primary"
            onClick={() => setActiveScreen("setup")}
          >
            Открыть мастер
          </Button>
        </div>
      )}

      <Card className="home-hero">
        <div className="home-hero-status">
          <span className={`home-status-dot status-${minecraftStatus}`} />
          <div>
            <h2>
              {serverRunning ? "Сервер запущен" : minecraftStatus === "stopping" ? "Сервер останавливается" : "Сервер остановлен"}
            </h2>
            <p>
              {serverRunning ? formatDuration(uptime) : "—"} · {playerCount}/
              {profile.data?.minecraft.max_players ?? 20} игроков · туннель{" "}
              <span className={tunnelRunning ? "ok" : "muted"}>
                {tunnelRunning ? "online" : frpcStatus}
              </span>
            </p>
          </div>
        </div>

        <div className="home-hero-address">
          <span className="eyebrow">Адрес для друзей</span>
          <div className="home-address-row">
            <strong>{connectAddress ?? "VPS не настроен"}</strong>
            {connectAddress && (
              <button type="button" className="ghost-btn" onClick={onCopyAddress}>
                <Copy size={14} /> копировать
              </button>
            )}
          </div>
          {profile.data?.minecraft.motd && <p>{profile.data.minecraft.motd}</p>}
        </div>

        <div className="home-hero-cta">
          {serverRunning ? (
            <Button
              variant="primary"
              icon={<Power size={18} />}
              disabled={stopAll.isPending}
              onClick={() => stopAll.mutate()}
            >
              Остановить сервер
            </Button>
          ) : (
            <Button
              variant="primary"
              icon={<Play size={18} />}
              disabled={startAll.isPending || setupIncomplete}
              onClick={() => startAll.mutate()}
            >
              Запустить сервер
            </Button>
          )}
          <OverflowMenu
            items={[
              {
                label: "Перезапустить",
                onClick: () => restart.mutate(),
                disabled: !serverRunning || restart.isPending
              },
              {
                label: "Перезаписать server.properties",
                onClick: () => writeProperties.mutate(),
                disabled: writeProperties.isPending
              },
              {
                label: "Создать eula.txt",
                onClick: () => writeEula.mutate(),
                disabled: writeEula.isPending
              },
              {
                label: "Только остановить туннель",
                onClick: async () => {
                  try {
                    await api.stopFrpc();
                    note("Туннель остановлен.");
                  } catch (err) {
                    fail(err);
                  }
                },
                disabled: !tunnelRunning
              },
              {
                label: "Принудительная остановка",
                danger: true,
                onClick: async () => {
                  try {
                    await api.stopMinecraft();
                    await api.stopFrpc();
                    queryClient.invalidateQueries();
                    note("Команды остановки отправлены.");
                  } catch (err) {
                    fail(err);
                  }
                }
              }
            ]}
          />
        </div>
      </Card>

      {(actionMessage || actionError) && (
        <div className={actionError ? "home-flash is-error" : "home-flash"}>
          {actionError ?? actionMessage}
        </div>
      )}

      <div className="home-quick-row">
        <Card className="home-quick-card">
          <div className="quick-head">
            <Cpu size={14} />
            <span>CPU сервера</span>
          </div>
          <strong>{latest?.server_cpu ?? 0}%</strong>
          <p className="muted">система {latest?.cpu ?? 0}%</p>
        </Card>
        <Card className="home-quick-card">
          <div className="quick-head">
            <MemoryStick size={14} />
            <span>RAM сервера</span>
          </div>
          <strong>{latest ? formatMb(latest.server_ram_mb) : "0 МБ"}</strong>
          <p className="muted">
            {ramTotalMb > 0
              ? `${formatMb(ramUsedMb)} / ${formatMb(ramTotalMb)}`
              : "система"}
          </p>
        </Card>
        <Card className="home-quick-card">
          <div className="quick-head">
            <Network size={14} />
            <span>Сеть</span>
          </div>
          <strong>{latest?.net_down_kbps ?? 0} КБ/с</strong>
          <p className="muted">↑ {latest?.net_up_kbps ?? 0} КБ/с</p>
        </Card>
        <Card className="home-quick-card">
          <div className="quick-head">
            <Users size={14} />
            <span>Игроки</span>
          </div>
          <strong>{playerCount}</strong>
          <p className="muted">{players.length ? players.join(", ") : "никого"}</p>
        </Card>
      </div>

      <Card className="home-secondary">
        <div className="home-secondary-row">
          <div>
            <span className="eyebrow">
              <Activity size={12} /> состояние
            </span>
            <strong>
              Minecraft: {minecraftStatus} · FRP: {frpcStatus}
            </strong>
          </div>
          <Button icon={<Terminal size={14} />} onClick={() => setConsoleOpen(true)}>
            Открыть консоль <kbd>~</kbd>
          </Button>
        </div>
      </Card>

      <Card className="home-footer">
        <div className="home-footer-row">
          <GaugeIcon size={14} />
          <span>Аптайм</span>
          <strong>{serverRunning ? formatDuration(uptime) : "—"}</strong>
          <RotateCcw
            size={14}
            className="muted-icon"
            onClick={() => queryClient.invalidateQueries()}
            role="button"
            aria-label="Обновить"
          />
        </div>
      </Card>
    </div>
  );
}

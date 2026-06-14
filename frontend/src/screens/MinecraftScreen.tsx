import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Cpu, FileCheck2, FileCode2, MemoryStick, Play, Save, Square, Users } from "lucide-react";

import { api } from "../lib/api";
import type { MinecraftConfig } from "../lib/types";
import { formatDuration, formatMb, useUptime } from "../lib/format";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Gauge, MetricArea } from "../components/ui/charts";
import { Console } from "../components/ui/Console";
import { Field, SelectInput, TextInput } from "../components/ui/Field";
import { ProfilePicker } from "../components/ui/ProfilePicker";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { StatusBadge } from "../components/ui/StatusBadge";
import { useAppStore } from "../store/app-store";

export function MinecraftScreen() {
  const queryClient = useQueryClient();
  const active = useQuery({
    queryKey: ["minecraft-profile-active"],
    queryFn: api.activeMinecraftProfile
  });
  const [config, setConfig] = useState<MinecraftConfig | null>(null);
  const [actionLines, setActionLines] = useState<string[]>([]);
  const logs = useAppStore((state) => state.minecraftLogs);
  const status = useAppStore((state) => state.minecraftStatus);
  const metrics = useAppStore((state) => state.metrics);
  const latest = useAppStore((state) => state.latest);
  const players = useAppStore((state) => state.players);
  const playerCount = useAppStore((state) => state.playerCount);
  const serverStartedAt = useAppStore((state) => state.serverStartedAt);
  const uptime = useUptime(serverStartedAt);

  useEffect(() => {
    if (active.data) setConfig(active.data.config);
  }, [active.data]);

  const save = useMutation({
    mutationFn: () => {
      if (!active.data?.profile.id || !config) throw new Error("Профиль Minecraft не выбран.");
      return api.saveMinecraftProfile(active.data.profile.id, config);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["minecraft-profile-active"] });
      queryClient.invalidateQueries({ queryKey: ["active-profile"] });
    }
  });

  const start = useMutation({ mutationFn: api.startMinecraft });
  const stop = useMutation({ mutationFn: api.stopMinecraft });
  const serverProperties = useMutation({ mutationFn: api.saveServerProperties });
  const eula = useMutation({ mutationFn: api.createEulaFile });
  const send = useMutation({ mutationFn: (command: string) => api.sendMinecraftCommand(command) });

  const runAction = (title: string, action: () => Promise<{ message: string }>) => {
    setActionLines((lines) => [...lines, `${title}...`]);
    action()
      .then((result) => setActionLines((lines) => [...lines, result.message]))
      .catch((error: Error) => setActionLines((lines) => [...lines, `Ошибка: ${error.message}`]));
  };

  if (active.isError)
    return (
      <div className="screen">
        Не удалось подключиться к бэкенду: {(active.error as Error).message}
      </div>
    );
  if (!config) return <div className="screen">Загрузка Minecraft-профиля...</div>;

  const serverRunning = status === "running";
  const maxPlayers = config.max_players || 20;
  const memLimitMb = parseMemory(config.xmx);

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Minecraft"
        title="Локальный сервер"
        description="Настройки запуска, живые графики ресурсов и интерактивная консоль команд."
        action={
          <div className="hero-actions">
            <StatusBadge status={status} label={`сервер: ${status}`} />
            <Button
              variant="primary"
              icon={<Play size={16} />}
              disabled={serverRunning || start.isPending}
              onClick={() => start.mutate()}
            >
              Запустить
            </Button>
            <Button
              icon={<Square size={16} />}
              disabled={!serverRunning || stop.isPending}
              onClick={() => stop.mutate()}
            >
              Остановить
            </Button>
          </div>
        }
      />

      <ProfilePicker
        label="Minecraft"
        queryKey={["minecraft-profiles"]}
        activeQueryKey={["minecraft-profile-active"]}
        listProfiles={api.minecraftProfiles}
        getActiveProfile={api.activeMinecraftProfile}
        createProfile={api.createMinecraftProfile}
        setActiveProfile={api.setActiveMinecraftProfile}
        renameProfile={api.renameMinecraftProfile}
        deleteProfile={api.deleteMinecraftProfile}
      />

      <div className="gauge-grid">
        <Card title="CPU сервера">
          <Gauge value={latest?.server_cpu ?? 0} label="java" color="#f472b6" />
        </Card>
        <Card title="RAM сервера">
          <Gauge
            value={latest?.server_ram_mb ?? 0}
            max={memLimitMb}
            unit=" МБ"
            label={`лимит ${formatMb(memLimitMb)}`}
            color="#f59e0b"
          />
        </Card>
        <Card title="Игроки">
          <Gauge value={playerCount} max={maxPlayers} unit="" label="онлайн" color="#34d399" />
        </Card>
        <Card title="Сводка">
          <div className="state-stack">
            <div className="state-row">
              <span>Аптайм</span>
              <strong>{serverRunning ? formatDuration(uptime) : "—"}</strong>
            </div>
            <div className="state-row">
              <span>CPU системы</span>
              <strong>{latest?.cpu ?? 0}%</strong>
            </div>
            <div className="state-row">
              <span>Игроки</span>
              <strong>{players.length ? players.join(", ") : "никого"}</strong>
            </div>
          </div>
        </Card>
      </div>

      <div className="two-columns">
        <Card title="Ресурсы сервера" eyebrow="Live" action={<MemoryStick size={16} />}>
          <MetricArea
            data={metrics}
            series={[
              { key: "server_ram_mb", label: "RAM (МБ)", color: "#f59e0b" },
              { key: "server_cpu", label: "CPU (%)", color: "#f472b6" }
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

      <Console
        title="Консоль Minecraft"
        lines={logs.slice(-220)}
        onSubmit={(command) => send.mutate(command)}
        disabled={!serverRunning}
        disabledHint="запустите сервер, чтобы вводить команды"
      />

      <div className="two-columns wide-left">
        <Card title="Сервер и запуск" action={<Cpu size={16} />}>
          <div className="form-grid">
            <Field label="Папка сервера">
              <TextInput value={config.server_dir} onChange={(e) => setConfig({ ...config, server_dir: e.target.value })} />
            </Field>
            <Field label="server.jar">
              <TextInput value={config.jar_path} onChange={(e) => setConfig({ ...config, jar_path: e.target.value })} />
            </Field>
            <Field label="Java path">
              <TextInput value={config.java_path} onChange={(e) => setConfig({ ...config, java_path: e.target.value })} />
            </Field>
            <Field label="Xms">
              <TextInput value={config.xms} onChange={(e) => setConfig({ ...config, xms: e.target.value })} />
            </Field>
            <Field label="Xmx">
              <TextInput value={config.xmx} onChange={(e) => setConfig({ ...config, xmx: e.target.value })} />
            </Field>
            <Field label="Порт">
              <TextInput
                type="number"
                value={config.mc_port}
                onChange={(e) => setConfig({ ...config, mc_port: Number(e.target.value) })}
              />
            </Field>
            <Field label="Тип сервера">
              <SelectInput
                value={config.server_type}
                onChange={(e) => setConfig({ ...config, server_type: e.target.value as MinecraftConfig["server_type"] })}
              >
                {["Vanilla", "Paper", "Fabric", "Forge", "NeoForge"].map((type) => (
                  <option key={type}>{type}</option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Версия Minecraft">
              <TextInput value={config.mc_version} onChange={(e) => setConfig({ ...config, mc_version: e.target.value })} />
            </Field>
            <Field label="Difficulty">
              <SelectInput
                value={config.difficulty}
                onChange={(e) => setConfig({ ...config, difficulty: e.target.value as MinecraftConfig["difficulty"] })}
              >
                {["peaceful", "easy", "normal", "hard"].map((value) => (
                  <option key={value}>{value}</option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Макс. игроков">
              <TextInput
                type="number"
                value={config.max_players}
                onChange={(e) => setConfig({ ...config, max_players: Number(e.target.value) })}
              />
            </Field>
            <Field label="MOTD">
              <TextInput value={config.motd} onChange={(e) => setConfig({ ...config, motd: e.target.value })} />
            </Field>
          </div>
          <div className="action-row">
            <Button icon={<Save size={16} />} onClick={() => save.mutate()} disabled={save.isPending}>
              Сохранить
            </Button>
            <Button
              icon={<FileCode2 size={16} />}
              onClick={() => runAction("Запись server.properties", () => serverProperties.mutateAsync())}
              disabled={serverProperties.isPending}
            >
              server.properties
            </Button>
            <Button
              icon={<FileCheck2 size={16} />}
              onClick={() => runAction("Создание eula.txt", () => eula.mutateAsync())}
              disabled={eula.isPending}
            >
              eula.txt
            </Button>
          </div>
        </Card>

        <Card title="Действия">
          <p className="muted">
            Быстрые команды отправляются в работающий сервер. Используйте консоль выше для любых
            команд (например <code>list</code>, <code>say</code>, <code>op</code>).
          </p>
          <div className="action-row">
            <Button disabled={!serverRunning} onClick={() => send.mutate("list")}>
              list
            </Button>
            <Button disabled={!serverRunning} onClick={() => send.mutate("say Привет от MineBridge!")}>
              say
            </Button>
            <Button disabled={!serverRunning} onClick={() => send.mutate("save-all")}>
              save-all
            </Button>
            <Button variant="danger" disabled={!serverRunning} onClick={() => stop.mutate()}>
              stop
            </Button>
          </div>
          {actionLines.length > 0 && <Console title="Действия Minecraft" lines={actionLines} />}
        </Card>
      </div>
    </div>
  );
}

function parseMemory(value: string): number {
  const match = /^(\d+(?:\.\d+)?)\s*([gGmMkK]?)/.exec(value.trim());
  if (!match) return 2048;
  const amount = Number(match[1]);
  const unit = match[2].toLowerCase();
  if (unit === "g") return Math.round(amount * 1024);
  if (unit === "k") return Math.max(1, Math.round(amount / 1024));
  return Math.round(amount || 2048);
}

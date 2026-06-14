import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileCheck2, FileCode2, Play, Save, Send, Square } from "lucide-react";

import { api } from "../lib/api";
import type { MinecraftConfig } from "../lib/types";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Field, SelectInput, TextInput } from "../components/ui/Field";
import { ProfilePicker } from "../components/ui/ProfilePicker";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { TerminalConsole } from "../components/ui/TerminalConsole";
import { useAppStore } from "../store/app-store";

export function MinecraftScreen() {
  const queryClient = useQueryClient();
  const active = useQuery({
    queryKey: ["minecraft-profile-active"],
    queryFn: api.activeMinecraftProfile
  });
  const [config, setConfig] = useState<MinecraftConfig | null>(null);
  const [command, setCommand] = useState("");
  const [actionLines, setActionLines] = useState<string[]>([]);
  const logs = useAppStore((state) => state.minecraftLogs);

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
  const send = useMutation({
    mutationFn: () => api.sendMinecraftCommand(command),
    onSuccess: () => setCommand("")
  });

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

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Minecraft"
        title="Локальный сервер"
        description="Настройка server.jar, памяти, server.properties и консоли команд."
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

      <div className="two-columns wide-left">
        <Card title="Сервер и запуск">
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
            <Button variant="primary" icon={<Play size={16} />} onClick={() => start.mutate()}>
              Запустить
            </Button>
            <Button icon={<Square size={16} />} onClick={() => stop.mutate()}>
              Остановить
            </Button>
          </div>
        </Card>

        <Card title="Команда серверу">
          <div className="command-box">
            <TextInput
              value={command}
              placeholder="say hello"
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && command.trim()) send.mutate();
              }}
            />
            <Button icon={<Send size={16} />} disabled={!command.trim()} onClick={() => send.mutate()}>
              Отправить
            </Button>
          </div>
          <TerminalConsole title="Minecraft logs" lines={logs} />
          {actionLines.length > 0 && <TerminalConsole title="Действия Minecraft" lines={actionLines} />}
        </Card>
      </div>
    </div>
  );
}

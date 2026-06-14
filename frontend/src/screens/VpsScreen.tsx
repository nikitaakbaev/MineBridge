import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CloudCog, FileCode2, Flame, Play, RotateCw, Save, ShieldCheck, Square } from "lucide-react";

import { api } from "../lib/api";
import type { VpsConfig } from "../lib/types";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Field, SelectInput, TextInput } from "../components/ui/Field";
import { ProfilePicker } from "../components/ui/ProfilePicker";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { TerminalConsole } from "../components/ui/TerminalConsole";
import { useAppStore } from "../store/app-store";

export function VpsScreen() {
  const queryClient = useQueryClient();
  const active = useQuery({ queryKey: ["vps-profile-active"], queryFn: api.activeVpsProfile });
  const [config, setConfig] = useState<VpsConfig | null>(null);
  const [password, setPassword] = useState("");
  const [actionLines, setActionLines] = useState<string[]>([]);
  const logs = useAppStore((state) => state.vpsLogs);

  useEffect(() => {
    if (active.data) setConfig(active.data.config);
  }, [active.data]);

  const save = useMutation({
    mutationFn: () => {
      if (!active.data?.profile.id || !config) throw new Error("VPS-профиль не выбран.");
      return api.saveVpsProfile(active.data.profile.id, config, password);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vps-profile-active"] });
      queryClient.invalidateQueries({ queryKey: ["active-profile"] });
    }
  });

  const ssh = useMutation({ mutationFn: () => api.checkSsh(password) });
  const install = useMutation({ mutationFn: () => api.installFrps(password) });
  const status = useMutation({ mutationFn: () => api.frpsStatus(password) });
  const start = useMutation({ mutationFn: () => api.startFrps(password) });
  const stop = useMutation({ mutationFn: () => api.stopFrps(password) });
  const restart = useMutation({ mutationFn: () => api.restartFrps(password) });
  const configFile = useMutation({ mutationFn: () => api.createFrpsConfig(password) });
  const firewall = useMutation({ mutationFn: () => api.openFirewall(password) });

  const runCommand = (
    title: string,
    action: () => Promise<{ stdout?: string; stderr?: string; message?: string }>
  ) => {
    setActionLines((lines) => [...lines, `${title}...`]);
    action()
      .then((result) => {
        const output = [result.message, result.stdout, result.stderr].filter(Boolean).join("\n");
        setActionLines((lines) => [...lines, output || "Готово."]);
      })
      .catch((error: Error) => setActionLines((lines) => [...lines, `Ошибка: ${error.message}`]));
  };

  if (active.isError)
    return (
      <div className="screen">
        Не удалось подключиться к бэкенду: {(active.error as Error).message}
      </div>
    );
  if (!config) return <div className="screen">Загрузка VPS-профиля...</div>;

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="VPS"
        title="Удалённый frps"
        description="SSH, установка frps, systemd и firewall остаются на Python backend."
      />

      <ProfilePicker
        label="VPS"
        queryKey={["vps-profiles"]}
        activeQueryKey={["vps-profile-active"]}
        listProfiles={api.vpsProfiles}
        getActiveProfile={api.activeVpsProfile}
        createProfile={api.createVpsProfile}
        setActiveProfile={api.setActiveVpsProfile}
        renameProfile={api.renameVpsProfile}
        deleteProfile={api.deleteVpsProfile}
      />

      <div className="two-columns wide-left">
        <Card title="Подключение и frps">
          <div className="form-grid">
            <Field label="VPS IP / host">
              <TextInput value={config.host} onChange={(e) => setConfig({ ...config, host: e.target.value })} />
            </Field>
            <Field label="SSH port">
              <TextInput type="number" value={config.ssh_port} onChange={(e) => setConfig({ ...config, ssh_port: Number(e.target.value) })} />
            </Field>
            <Field label="SSH username">
              <TextInput value={config.username} onChange={(e) => setConfig({ ...config, username: e.target.value })} />
            </Field>
            <Field label="Auth type">
              <SelectInput value={config.auth_type} onChange={(e) => setConfig({ ...config, auth_type: e.target.value as VpsConfig["auth_type"] })}>
                <option value="password">password</option>
                <option value="private_key">private_key</option>
              </SelectInput>
            </Field>
            {config.auth_type === "password" ? (
              <Field label="Password" hint="Не отправляется в React-хранилище">
                <TextInput type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
              </Field>
            ) : (
              <Field label="Private key path">
                <TextInput value={config.private_key_path} onChange={(e) => setConfig({ ...config, private_key_path: e.target.value })} />
              </Field>
            )}
            <Field label="Папка frps">
              <TextInput value={config.install_dir} onChange={(e) => setConfig({ ...config, install_dir: e.target.value })} />
            </Field>
            <Field label="Порт frps">
              <TextInput type="number" value={config.frps_bind_port} onChange={(e) => setConfig({ ...config, frps_bind_port: Number(e.target.value) })} />
            </Field>
            <Field label="Dashboard port">
              <TextInput type="number" value={config.dashboard_port} onChange={(e) => setConfig({ ...config, dashboard_port: Number(e.target.value) })} />
            </Field>
          </div>
          <div className="action-row">
            <Button icon={<Save size={16} />} onClick={() => save.mutate()}>
              Сохранить
            </Button>
            <Button
              icon={<ShieldCheck size={16} />}
              onClick={() => runCommand("Проверка SSH", () => ssh.mutateAsync())}
              disabled={ssh.isPending}
            >
              Проверить SSH
            </Button>
            <Button
              icon={<CloudCog size={16} />}
              onClick={() => runCommand("Установка frps", () => install.mutateAsync())}
              disabled={install.isPending}
            >
              Установить frps
            </Button>
            <Button
              icon={<FileCode2 size={16} />}
              onClick={() => runCommand("Создание frps.toml", () => configFile.mutateAsync())}
              disabled={configFile.isPending}
            >
              frps.toml
            </Button>
            <Button
              variant="primary"
              icon={<Play size={16} />}
              onClick={() => runCommand("Запуск frps", () => start.mutateAsync())}
              disabled={start.isPending}
            >
              Запустить
            </Button>
            <Button
              icon={<Square size={16} />}
              onClick={() => runCommand("Остановка frps", () => stop.mutateAsync())}
              disabled={stop.isPending}
            >
              Остановить
            </Button>
            <Button
              icon={<RotateCw size={16} />}
              onClick={() => runCommand("Перезапуск frps", () => restart.mutateAsync())}
              disabled={restart.isPending}
            >
              Перезапустить
            </Button>
            <Button
              icon={<Flame size={16} />}
              onClick={() => runCommand("Открытие firewall", () => firewall.mutateAsync())}
              disabled={firewall.isPending}
            >
              Firewall
            </Button>
            <Button onClick={() => runCommand("Статус frps", () => status.mutateAsync())} disabled={status.isPending}>
              Статус
            </Button>
          </div>
        </Card>

        <TerminalConsole
          title="VPS output"
          lines={[
            ...logs,
            ...actionLines,
            ssh.data?.stdout || "",
            status.data?.stdout || "",
            install.data?.message || ""
          ].filter(Boolean)}
        />
      </div>
    </div>
  );
}

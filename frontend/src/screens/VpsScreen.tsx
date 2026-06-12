import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CloudCog, Play, Save, ShieldCheck, Square } from "lucide-react";

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
  const logs = useAppStore((state) => state.vpsLogs);

  useEffect(() => {
    if (active.data) setConfig(active.data.config);
  }, [active.data]);

  const save = useMutation({
    mutationFn: () => {
      if (!active.data?.profile.id || !config) throw new Error("VPS-профиль не выбран.");
      return api.saveVpsProfile(active.data.profile.id, config);
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
            <Button icon={<ShieldCheck size={16} />} onClick={() => ssh.mutate()}>
              Проверить SSH
            </Button>
            <Button icon={<CloudCog size={16} />} onClick={() => install.mutate()}>
              Установить frps
            </Button>
            <Button variant="primary" icon={<Play size={16} />} onClick={() => start.mutate()}>
              Запустить
            </Button>
            <Button icon={<Square size={16} />} onClick={() => stop.mutate()}>
              Остановить
            </Button>
            <Button onClick={() => status.mutate()}>Статус</Button>
          </div>
        </Card>

        <TerminalConsole
          title="VPS output"
          lines={[
            ...logs,
            ssh.data?.stdout || "",
            status.data?.stdout || "",
            install.data?.message || ""
          ].filter(Boolean)}
        />
      </div>
    </div>
  );
}

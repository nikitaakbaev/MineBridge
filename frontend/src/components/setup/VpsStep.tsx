import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, ShieldCheck } from "lucide-react";

import { api } from "../../lib/api";
import { isNetworkFetchError } from "../../lib/errors";
import { useDebouncedSave } from "../../lib/useDebouncedSave";
import type { VpsConfig } from "../../lib/types";
import { useAppStore } from "../../store/app-store";
import { Button } from "../ui/Button";
import { Field, SelectInput, TextInput } from "../ui/Field";
import { TerminalConsole } from "../ui/TerminalConsole";

type VpsStepProps = {
  onAdvance: () => void;
};

export function VpsStep({ onAdvance }: VpsStepProps) {
  const queryClient = useQueryClient();
  const backendConnected = useAppStore((state) => state.backendConnected);
  const active = useQuery({
    queryKey: ["vps-profile-active"],
    queryFn: api.activeVpsProfile,
    enabled: backendConnected
  });

  const [config, setConfig] = useState<VpsConfig | null>(null);
  const [password, setPassword] = useState("");
  const [logs, setLogs] = useState<string[]>([]);
  const [stage1Done, setStage1Done] = useState(false);

  useEffect(() => {
    if (active.data) {
      setConfig(active.data.config);
      setStage1Done(Boolean(active.data.config.host && active.data.config.username));
    }
  }, [active.data]);

  const profileId = active.data?.profile.id ?? null;

  const saveProfile = useMutation({
    mutationFn: (next: VpsConfig) => {
      if (!profileId) throw new Error("VPS-профиль не выбран.");
      return api.saveVpsProfile(profileId, next, password);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vps-profile-active"] });
      queryClient.invalidateQueries({ queryKey: ["active-profile"] });
    }
  });

  const debounceTarget = useMemo(
    () => (config ? { config, password } : null),
    [config, password]
  );

  useDebouncedSave(
    debounceTarget,
    (value) => {
      if (!value) return;
      if (!profileId) return;
      saveProfile.mutate(value.config);
    },
    400
  );

  const installPipeline = useMutation({
    mutationFn: async () => {
      if (!config) throw new Error("Заполните поля VPS.");
      setLogs((lines) => [...lines, "Сохранение профиля VPS..."]);
      await api.saveVpsProfile(profileId!, config, password);
      setLogs((lines) => [...lines, "Проверка SSH..."]);
      const ssh = await api.checkSsh(password);
      setLogs((lines) => [
        ...lines,
        `SSH exit=${ssh.exit_status ?? "?"}: ${ssh.stdout || ssh.stderr || "ok"}`
      ]);
      if (ssh.exit_status && ssh.exit_status !== 0) {
        throw new Error(ssh.stderr || ssh.stdout || "SSH вернул не нулевой код.");
      }
      setLogs((lines) => [...lines, "Установка frps на VPS..."]);
      const install = await api.installFrps(password);
      setLogs((lines) => [...lines, install.message]);
      setLogs((lines) => [...lines, "Открытие firewall..."]);
      const fw = await api.openFirewall(password);
      setLogs((lines) => [...lines, fw.message]);
      return install;
    },
    onSuccess: async () => {
      setStage1Done(true);
      await api.setSetupStatus({ current_step: "tunnel" });
      onAdvance();
    },
    onError: (error: Error) => {
      setLogs((lines) => [...lines, `Ошибка: ${error.message}`]);
    }
  });

  if (!backendConnected) {
    return (
      <div className="setup-step-body">
        <header className="setup-step-head">
          <h2>VPS-сервер</h2>
          <p className="muted">Ждём соединение с backend.</p>
        </header>
        <div className="empty-state">Backend starting...</div>
      </div>
    );
  }

  if (active.isError) {
    if (isNetworkFetchError(active.error)) {
      return (
        <div className="setup-step-body">
          <header className="setup-step-head">
            <h2>VPS-сервер</h2>
            <p className="muted">Ждём соединение с backend.</p>
          </header>
          <div className="empty-state">Backend starting...</div>
        </div>
      );
    }
    return (
      <div className="setup-step-body">
        <header className="setup-step-head">
          <h2>VPS-сервер</h2>
          <p className="muted">Не удалось загрузить VPS-профиль.</p>
        </header>
        <div className="error-box">{(active.error as Error).message}</div>
        <Button onClick={() => active.refetch()}>Повторить</Button>
      </div>
    );
  }

  if (!config) return <div className="screen">Загрузка VPS-профиля...</div>;

  const update = (patch: Partial<VpsConfig>) =>
    setConfig((current) => (current ? { ...current, ...patch } : current));

  return (
    <div className="setup-step-body">
      <header className="setup-step-head">
        <h2>VPS-сервер</h2>
        <p className="muted">
          Введите доступ к VPS, на котором будет работать frps. Поля автосохраняются.
        </p>
      </header>

      <div className="form-grid">
        <Field label="Адрес VPS">
          <TextInput
            value={config.host}
            placeholder="vps.example.com"
            onChange={(e) => update({ host: e.target.value })}
          />
        </Field>
        <Field label="SSH порт">
          <TextInput
            type="number"
            value={config.ssh_port}
            onChange={(e) => update({ ssh_port: Number(e.target.value) })}
          />
        </Field>
        <Field label="SSH пользователь">
          <TextInput
            value={config.username}
            onChange={(e) => update({ username: e.target.value })}
          />
        </Field>
        <Field label="Тип авторизации">
          <SelectInput
            value={config.auth_type}
            onChange={(e) => update({ auth_type: e.target.value as VpsConfig["auth_type"] })}
          >
            <option value="password">Пароль</option>
            <option value="private_key">SSH-ключ</option>
          </SelectInput>
        </Field>
        {config.auth_type === "password" ? (
          <Field label="Пароль (только в памяти)">
            <TextInput
              type="password"
              value={password}
              autoComplete="new-password"
              onChange={(e) => setPassword(e.target.value)}
            />
          </Field>
        ) : (
          <Field label="Путь к private key">
            <TextInput
              value={config.private_key_path}
              onChange={(e) => update({ private_key_path: e.target.value })}
            />
          </Field>
        )}
        <Field label="Папка установки на VPS">
          <TextInput
            value={config.install_dir}
            onChange={(e) => update({ install_dir: e.target.value })}
          />
        </Field>
        <Field label="Порт frps (bind)">
          <TextInput
            type="number"
            value={config.frps_bind_port}
            onChange={(e) => update({ frps_bind_port: Number(e.target.value) })}
          />
        </Field>
      </div>

      <div className="setup-action-row">
        <Button
          variant="primary"
          icon={<ShieldCheck size={16} />}
          disabled={
            installPipeline.isPending ||
            !config.host ||
            !config.username ||
            (config.auth_type === "password" && !password)
          }
          onClick={() => installPipeline.mutate()}
        >
          Проверить и установить frps
        </Button>
        {stage1Done && (
          <span className="setup-success">
            <CheckCircle2 size={16} /> готово
          </span>
        )}
      </div>

      {logs.length > 0 && <TerminalConsole title="Установка VPS" lines={logs.slice(-150)} />}
    </div>
  );
}

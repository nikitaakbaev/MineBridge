import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, KeyRound, Waypoints } from "lucide-react";

import { api } from "../../lib/api";
import { useDebouncedSave } from "../../lib/useDebouncedSave";
import type { TunnelConfig } from "../../lib/types";
import { Button } from "../ui/Button";
import { Field, TextInput } from "../ui/Field";
import { TerminalConsole } from "../ui/TerminalConsole";

type TunnelStepProps = {
  onAdvance: () => void;
};

export function TunnelStep({ onAdvance }: TunnelStepProps) {
  const queryClient = useQueryClient();
  const active = useQuery({
    queryKey: ["tunnel-profile-active"],
    queryFn: api.activeTunnelProfile
  });
  const vps = useQuery({
    queryKey: ["vps-profile-active"],
    queryFn: api.activeVpsProfile
  });

  const [config, setConfig] = useState<TunnelConfig | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [stage2Done, setStage2Done] = useState(false);

  useEffect(() => {
    if (!active.data) return;
    const incoming = { ...active.data.config };
    if (!incoming.frp_server_addr && vps.data?.config.host) {
      incoming.frp_server_addr = vps.data.config.host;
    }
    setConfig(incoming);
    setStage2Done(Boolean(incoming.frp_token));
  }, [active.data, vps.data]);

  const profileId = active.data?.profile.id ?? null;

  const saveProfile = useMutation({
    mutationFn: (next: TunnelConfig) => {
      if (!profileId) throw new Error("Tunnel-профиль не выбран.");
      return api.saveTunnelProfile(profileId, next);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tunnel-profile-active"] });
      queryClient.invalidateQueries({ queryKey: ["active-profile"] });
    }
  });

  useDebouncedSave(
    config,
    (value) => {
      if (!value || !profileId) return;
      saveProfile.mutate(value);
    },
    400
  );

  const debounceKey = useMemo(() => JSON.stringify(config), [config]);
  void debounceKey;

  const installPipeline = useMutation({
    mutationFn: async () => {
      if (!config || !profileId) throw new Error("Туннель не настроен.");
      let next = { ...config };
      if (!next.frp_token) {
        setLogs((lines) => [...lines, "Генерация токена..."]);
        const token = await api.generateFrpToken();
        next = { ...next, frp_token: token.message };
        setLogs((lines) => [...lines, `Токен: ${token.message.slice(0, 8)}…`]);
      }
      setLogs((lines) => [...lines, "Сохранение профиля туннеля..."]);
      await api.saveTunnelProfile(profileId, next);
      setConfig(next);
      setLogs((lines) => [...lines, "Скачивание frpc..."]);
      const dl = await api.downloadFrpc();
      setLogs((lines) => [...lines, dl.message]);
      setLogs((lines) => [...lines, "Запись frpc.toml..."]);
      const cfg = await api.createFrpcConfig();
      setLogs((lines) => [...lines, cfg.message]);
      return cfg;
    },
    onSuccess: async () => {
      setStage2Done(true);
      await api.setSetupStatus({ current_step: "server" });
      onAdvance();
    },
    onError: (error: Error) => {
      setLogs((lines) => [...lines, `Ошибка: ${error.message}`]);
    }
  });

  if (active.isError)
    return <div className="screen">Не удалось загрузить туннель: {(active.error as Error).message}</div>;
  if (!config) return <div className="screen">Загрузка туннеля...</div>;

  const update = (patch: Partial<TunnelConfig>) =>
    setConfig((current) => (current ? { ...current, ...patch } : current));

  return (
    <div className="setup-step-body">
      <header className="setup-step-head">
        <h2>FRP-туннель</h2>
        <p className="muted">
          Этот шаг настраивает локальный frpc, который соединит сервер с VPS. Поля
          автосохраняются.
        </p>
      </header>

      <div className="form-grid">
        <Field label="Адрес FRP-сервера">
          <TextInput
            value={config.frp_server_addr}
            placeholder={vps.data?.config.host || "vps.example.com"}
            onChange={(e) => update({ frp_server_addr: e.target.value })}
          />
        </Field>
        <Field label="Bind-порт frps">
          <TextInput
            type="number"
            value={config.frp_server_bind_port}
            onChange={(e) => update({ frp_server_bind_port: Number(e.target.value) })}
          />
        </Field>
        <Field label="Локальный порт сервера">
          <TextInput
            type="number"
            value={config.local_port}
            onChange={(e) => update({ local_port: Number(e.target.value) })}
          />
        </Field>
        <Field label="Внешний порт (для друзей)">
          <TextInput
            type="number"
            value={config.remote_port}
            onChange={(e) => update({ remote_port: Number(e.target.value) })}
          />
        </Field>
        <Field label="Токен">
          <div className="path-input">
            <TextInput
              type="password"
              value={config.frp_token}
              onChange={(e) => update({ frp_token: e.target.value })}
            />
            <Button
              icon={<KeyRound size={16} />}
              onClick={async () => {
                const token = await api.generateFrpToken();
                update({ frp_token: token.message });
              }}
            >
              Сгенерировать
            </Button>
          </div>
        </Field>
      </div>

      <div className="setup-action-row">
        <Button
          variant="primary"
          icon={<Waypoints size={16} />}
          disabled={installPipeline.isPending || !config.frp_server_addr}
          onClick={() => installPipeline.mutate()}
        >
          Скачать frpc и записать конфиг
        </Button>
        {stage2Done && (
          <span className="setup-success">
            <CheckCircle2 size={16} /> готово
          </span>
        )}
      </div>

      {logs.length > 0 && <TerminalConsole title="Установка туннеля" lines={logs.slice(-150)} />}
    </div>
  );
}

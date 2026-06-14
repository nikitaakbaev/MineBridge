import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileCode2, KeyRound, Play, ShieldCheck, Square } from "lucide-react";

import { api } from "../lib/api";
import type { TunnelConfig } from "../lib/types";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Field, TextInput } from "../components/ui/Field";
import { ProfilePicker } from "../components/ui/ProfilePicker";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { TerminalConsole } from "../components/ui/TerminalConsole";
import { useAppStore } from "../store/app-store";

export function TunnelsScreen() {
  const queryClient = useQueryClient();
  const active = useQuery({ queryKey: ["tunnel-profile-active"], queryFn: api.activeTunnelProfile });
  const [config, setConfig] = useState<TunnelConfig | null>(null);
  const [actionLines, setActionLines] = useState<string[]>([]);
  const logs = useAppStore((state) => state.frpcLogs);

  useEffect(() => {
    if (active.data) setConfig(active.data.config);
  }, [active.data]);

  const save = useMutation({
    mutationFn: () => {
      if (!active.data?.profile.id || !config) throw new Error("frpc-профиль не выбран.");
      return api.saveTunnelProfile(active.data.profile.id, config);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tunnel-profile-active"] });
      queryClient.invalidateQueries({ queryKey: ["active-profile"] });
    }
  });
  const makeConfig = useMutation({ mutationFn: api.createFrpcConfig });
  const download = useMutation({ mutationFn: api.downloadFrpc });
  const start = useMutation({ mutationFn: api.startFrpc });
  const stop = useMutation({ mutationFn: api.stopFrpc });
  const check = useMutation({ mutationFn: api.checkFrpcPort });
  const token = useMutation({ mutationFn: api.generateFrpToken });

  const runAction = (title: string, action: () => Promise<{ message: string }>) => {
    setActionLines((lines) => [...lines, `${title}...`]);
    action()
      .then((result) => setActionLines((lines) => [...lines, result.message]))
      .catch((error: Error) => setActionLines((lines) => [...lines, `Ошибка: ${error.message}`]));
  };

  const generateToken = () => {
    setActionLines((lines) => [...lines, "Генерация FRP token..."]);
    token
      .mutateAsync()
      .then((result) => {
        setConfig((current) => (current ? { ...current, frp_token: result.message } : current));
        setActionLines((lines) => [...lines, "FRP token создан. Сохраните профиль, чтобы закрепить его."]);
      })
      .catch((error: Error) => setActionLines((lines) => [...lines, `Ошибка: ${error.message}`]));
  };

  if (active.isError)
    return (
      <div className="screen">
        Не удалось подключиться к бэкенду: {(active.error as Error).message}
      </div>
    );
  if (!config) return <div className="screen">Загрузка frpc-профиля...</div>;

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="FRP tunnel"
        title="Публичный доступ без лишней сложности"
        description="Локальный frpc подключает Minecraft к frps на VPS и открывает друзьям один адрес."
      />

      <ProfilePicker
        label="frpc"
        queryKey={["tunnel-profiles"]}
        activeQueryKey={["tunnel-profile-active"]}
        listProfiles={api.tunnelProfiles}
        getActiveProfile={api.activeTunnelProfile}
        createProfile={api.createTunnelProfile}
        setActiveProfile={api.setActiveTunnelProfile}
        renameProfile={api.renameTunnelProfile}
        deleteProfile={api.deleteTunnelProfile}
      />

      <div className="two-columns wide-left">
        <Card title="Настройки туннеля">
          <div className="form-grid">
            <Field label="Локальный IP">
              <TextInput value={config.local_ip} onChange={(e) => setConfig({ ...config, local_ip: e.target.value })} />
            </Field>
            <Field label="Локальный порт">
              <TextInput type="number" value={config.local_port} onChange={(e) => setConfig({ ...config, local_port: Number(e.target.value) })} />
            </Field>
            <Field label="Публичный порт">
              <TextInput type="number" value={config.remote_port} onChange={(e) => setConfig({ ...config, remote_port: Number(e.target.value) })} />
            </Field>
            <Field label="Адрес VPS / frps">
              <TextInput value={config.frp_server_addr} onChange={(e) => setConfig({ ...config, frp_server_addr: e.target.value })} />
            </Field>
            <Field label="Порт frps">
              <TextInput type="number" value={config.frp_server_bind_port} onChange={(e) => setConfig({ ...config, frp_server_bind_port: Number(e.target.value) })} />
            </Field>
            <Field label="FRP token">
              <TextInput type="password" value={config.frp_token} onChange={(e) => setConfig({ ...config, frp_token: e.target.value })} />
            </Field>
          </div>
          <div className="action-row">
            <Button onClick={() => save.mutate()}>Сохранить</Button>
            <Button icon={<KeyRound size={16} />} onClick={generateToken} disabled={token.isPending}>
              Token
            </Button>
            <Button
              icon={<FileCode2 size={16} />}
              onClick={() => runAction("Создание frpc.toml", () => makeConfig.mutateAsync())}
              disabled={makeConfig.isPending}
            >
              frpc.toml
            </Button>
            <Button
              icon={<Download size={16} />}
              onClick={() => runAction("Скачивание frpc", () => download.mutateAsync())}
              disabled={download.isPending}
            >
              Скачать frpc
            </Button>
            <Button
              variant="primary"
              icon={<Play size={16} />}
              onClick={() => runAction("Запуск frpc", () => start.mutateAsync())}
              disabled={start.isPending}
            >
              Запустить
            </Button>
            <Button
              icon={<Square size={16} />}
              onClick={() => runAction("Остановка frpc", () => stop.mutateAsync())}
              disabled={stop.isPending}
            >
              Остановить
            </Button>
            <Button
              icon={<ShieldCheck size={16} />}
              onClick={() => runAction("Проверка внешнего порта", () => check.mutateAsync())}
              disabled={check.isPending}
            >
              Проверить порт
            </Button>
          </div>
        </Card>

        <TerminalConsole title="frpc logs" lines={[...actionLines, ...logs]} />
      </div>
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  FolderOpen,
  ListChecks,
  ScanSearch,
  Wand2
} from "lucide-react";

import { api } from "../../lib/api";
import { useDebouncedSave } from "../../lib/useDebouncedSave";
import type {
  DiagnosticResult,
  JavaInstallation,
  MinecraftConfig
} from "../../lib/types";
import { pickDirectory, pickFile } from "../../lib/dialog";
import { Button } from "../ui/Button";
import { Field, SelectInput, TextInput } from "../ui/Field";
import { JavaPicker } from "../ui/JavaPicker";
import { StatusBadge } from "../ui/StatusBadge";

const LAUNCHER_FILTERS = [
  { name: "Запуск сервера", extensions: ["jar", "sh", "bash", "bat", "cmd", "ps1"] },
  { name: "Все файлы", extensions: ["*"] }
];

const JAVA_FILTERS = [
  { name: "Java", extensions: ["exe", ""] },
  { name: "Все файлы", extensions: ["*"] }
];

type ServerStepProps = {
  onAdvance: () => void;
};

export function ServerStep({ onAdvance }: ServerStepProps) {
  const queryClient = useQueryClient();
  const active = useQuery({
    queryKey: ["minecraft-profile-active"],
    queryFn: api.activeMinecraftProfile
  });

  const [config, setConfig] = useState<MinecraftConfig | null>(null);
  const [diagnostics, setDiagnostics] = useState<DiagnosticResult[] | null>(null);
  const [actionLines, setActionLines] = useState<string[]>([]);
  const [javaInstallations, setJavaInstallations] = useState<JavaInstallation[]>([]);
  const [javaPickerOpen, setJavaPickerOpen] = useState(false);

  useEffect(() => {
    if (active.data) setConfig(active.data.config);
  }, [active.data]);

  const profileId = active.data?.profile.id ?? null;

  const saveProfile = useMutation({
    mutationFn: (next: MinecraftConfig) => {
      if (!profileId) throw new Error("Профиль не выбран.");
      return api.saveMinecraftProfile(profileId, next);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["minecraft-profile-active"] });
      queryClient.invalidateQueries({ queryKey: ["active-profile"] });
    }
  });

  useDebouncedSave(config, (value) => {
    if (!value || !profileId) return;
    saveProfile.mutate(value);
  });

  const note = (line: string) =>
    setActionLines((lines) => [...lines.slice(-50), line]);

  const update = (patch: Partial<MinecraftConfig>) =>
    setConfig((current) => (current ? { ...current, ...patch } : current));

  const autoDetectLauncher = async (serverDir: string) => {
    if (!serverDir) return;
    note(`Автопоиск файла запуска в ${serverDir}...`);
    try {
      const candidates = await api.detectLaunchers(serverDir);
      if (candidates.length === 0) {
        note("Файл запуска не найден.");
        return;
      }
      update({ jar_path: candidates[0].path });
      note(
        `Файл запуска: ${candidates[0].path}` +
          (candidates.length > 1 ? ` (ещё вариантов: ${candidates.length - 1})` : "")
      );
    } catch (err) {
      note(`Ошибка автопоиска: ${(err as Error).message}`);
    }
  };

  const handlePickServerDir = async () => {
    if (!config) return;
    const picked = await pickDirectory({ title: "Выберите папку Minecraft-сервера" });
    if (!picked) return;
    update({ server_dir: picked });
    await autoDetectLauncher(picked);
  };

  const handlePickJar = async () => {
    if (!config) return;
    const picked = await pickFile({
      title: "Файл запуска (.jar / .sh / .bat)",
      defaultPath: config.server_dir || config.jar_path,
      filters: LAUNCHER_FILTERS
    });
    if (!picked) return;
    update({ jar_path: picked });
  };

  const handleAutoDetectJava = async () => {
    note("Поиск Java...");
    try {
      const installations = await api.detectJava();
      setJavaInstallations(installations);
      if (installations.length === 0) {
        note("Java не найдена.");
        return;
      }
      if (installations.length === 1) {
        update({ java_path: installations[0].path });
        note(`Найдена Java ${installations[0].version}: ${installations[0].path}`);
        return;
      }
      setJavaPickerOpen(true);
    } catch (err) {
      note(`Ошибка поиска Java: ${(err as Error).message}`);
    }
  };

  const handlePickJavaPath = async () => {
    if (!config) return;
    const picked = await pickFile({
      title: "Выберите java executable",
      defaultPath: config.java_path,
      filters: JAVA_FILTERS
    });
    if (!picked) return;
    update({ java_path: picked });
  };

  const runDiagnostics = useMutation({
    mutationFn: api.diagnostics,
    onSuccess: (results) => {
      setDiagnostics(results);
    }
  });

  useEffect(() => {
    runDiagnostics.mutate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const acceptEula = async () => {
    try {
      const eula = await api.createEulaFile();
      note(`eula.txt создан: ${eula.message}`);
      const props = await api.saveServerProperties();
      note(`server.properties: ${props.message}`);
      runDiagnostics.mutate();
    } catch (err) {
      note(`Ошибка: ${(err as Error).message}`);
    }
  };

  const advance = useMutation({
    mutationFn: async () => api.setSetupStatus({ current_step: "done" }),
    onSuccess: onAdvance
  });

  const allOk = useMemo(
    () => diagnostics !== null && diagnostics.every((r) => r.status !== "ERROR"),
    [diagnostics]
  );

  if (active.isError)
    return <div className="screen">Не удалось загрузить профиль: {(active.error as Error).message}</div>;
  if (!config) return <div className="screen">Загрузка профиля...</div>;

  return (
    <div className="setup-step-body">
      <header className="setup-step-head">
        <h2>Minecraft-сервер</h2>
        <p className="muted">
          Выберите папку сервера. Файл запуска и Java определяются автоматически.
        </p>
      </header>

      <div className="form-grid">
        <Field label="Папка сервера">
          <div className="path-input">
            <TextInput
              value={config.server_dir}
              placeholder="Не выбрано"
              onChange={(e) => update({ server_dir: e.target.value })}
            />
            <Button icon={<FolderOpen size={16} />} onClick={handlePickServerDir}>
              Выбрать
            </Button>
          </div>
        </Field>
        <Field label="Файл запуска (.jar / .sh / .bat)">
          <div className="path-input">
            <TextInput
              value={config.jar_path}
              placeholder="server.jar или run.sh"
              onChange={(e) => update({ jar_path: e.target.value })}
            />
            <Button icon={<FolderOpen size={16} />} onClick={handlePickJar}>
              Выбрать
            </Button>
            <Button
              icon={<ScanSearch size={16} />}
              onClick={() => autoDetectLauncher(config.server_dir)}
            >
              Найти
            </Button>
          </div>
        </Field>
        <Field label="Java path">
          <div className="path-input">
            <TextInput
              value={config.java_path}
              placeholder="Из PATH"
              onChange={(e) => update({ java_path: e.target.value })}
            />
            <Button icon={<FolderOpen size={16} />} onClick={handlePickJavaPath}>
              Выбрать
            </Button>
            <Button icon={<Wand2 size={16} />} onClick={handleAutoDetectJava}>
              Авто
            </Button>
          </div>
        </Field>
        <Field label="Xms">
          <TextInput value={config.xms} onChange={(e) => update({ xms: e.target.value })} />
        </Field>
        <Field label="Xmx">
          <TextInput value={config.xmx} onChange={(e) => update({ xmx: e.target.value })} />
        </Field>
        <Field label="Порт">
          <TextInput
            type="number"
            value={config.mc_port}
            onChange={(e) => update({ mc_port: Number(e.target.value) })}
          />
        </Field>
        <Field label="Тип сервера">
          <SelectInput
            value={config.server_type}
            onChange={(e) =>
              update({ server_type: e.target.value as MinecraftConfig["server_type"] })
            }
          >
            {["Vanilla", "Paper", "Fabric", "Forge", "NeoForge"].map((type) => (
              <option key={type}>{type}</option>
            ))}
          </SelectInput>
        </Field>
        <Field label="Difficulty">
          <SelectInput
            value={config.difficulty}
            onChange={(e) =>
              update({ difficulty: e.target.value as MinecraftConfig["difficulty"] })
            }
          >
            {["peaceful", "easy", "normal", "hard"].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </SelectInput>
        </Field>
        <Field label="online-mode">
          <SelectInput
            value={config.online_mode ? "true" : "false"}
            onChange={(e) => update({ online_mode: e.target.value === "true" })}
          >
            <option value="true">true (только лицензия)</option>
            <option value="false">false (пиратки тоже)</option>
          </SelectInput>
        </Field>
        <Field label="Макс. игроков">
          <TextInput
            type="number"
            value={config.max_players}
            onChange={(e) => update({ max_players: Number(e.target.value) })}
          />
        </Field>
        <Field label="MOTD">
          <TextInput value={config.motd} onChange={(e) => update({ motd: e.target.value })} />
        </Field>
      </div>

      <div className="setup-action-row">
        <Button onClick={acceptEula}>Принять EULA и записать server.properties</Button>
        <Button
          icon={<ListChecks size={16} />}
          onClick={() => runDiagnostics.mutate()}
          disabled={runDiagnostics.isPending}
        >
          Проверить ещё раз
        </Button>
      </div>

      {diagnostics && (
        <div className="diagnostics-card">
          {diagnostics.map((row) => (
            <div className="diagnostics-row" key={`${row.name}-${row.description}`}>
              <StatusBadge status={row.status} label={row.status} />
              <strong>{row.name}</strong>
              <span className="muted">{row.description}</span>
            </div>
          ))}
        </div>
      )}

      {actionLines.length > 0 && (
        <pre className="setup-log">{actionLines.join("\n")}</pre>
      )}

      <div className="setup-action-row">
        <Button
          variant="primary"
          icon={<CheckCircle2 size={16} />}
          disabled={!allOk || advance.isPending}
          onClick={() => advance.mutate()}
        >
          Всё готово, перейти к запуску
        </Button>
        {!allOk && diagnostics && (
          <span className="muted">Исправьте ошибки диагностики, чтобы продолжить.</span>
        )}
      </div>

      <JavaPicker
        open={javaPickerOpen}
        installations={javaInstallations}
        current={config.java_path}
        onSelect={(installation) => {
          update({ java_path: installation.path });
          setJavaPickerOpen(false);
          note(`Выбрана Java ${installation.version}: ${installation.path}`);
        }}
        onClose={() => setJavaPickerOpen(false)}
      />
    </div>
  );
}

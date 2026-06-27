import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Play, Sparkles } from "lucide-react";

import { api } from "../../lib/api";
import { isNetworkFetchError } from "../../lib/errors";
import type { SetupState } from "../../lib/types";
import { useAppStore } from "../../store/app-store";
import { Button } from "../ui/Button";

export function DoneStep() {
  const queryClient = useQueryClient();
  const backendConnected = useAppStore((state) => state.backendConnected);
  const profile = useQuery({
    queryKey: ["active-profile"],
    queryFn: api.activeProfile,
    enabled: backendConnected
  });
  const setActiveScreen = useAppStore((state) => state.setActiveScreen);
  const setSetupStatus = useAppStore((state) => state.setSetupStatus);

  const launch = useMutation({
    mutationFn: async () => {
      await api.startMinecraft();
      await api.startFrpc();
      const next = await api.setSetupStatus({ completed: true, current_step: "done" });
      return next;
    },
    onSuccess: (next: SetupState) => {
      setSetupStatus(next);
      queryClient.setQueryData(["setup-status"], next);
      queryClient.invalidateQueries({ queryKey: ["setup-status"] });
      setActiveScreen("home");
    }
  });

  const address = profile.data?.vps.host
    ? `${profile.data.vps.host}:${profile.data.tunnel.remote_port}`
    : null;

  if (!backendConnected) {
    return (
      <div className="setup-step-body">
        <header className="setup-step-head">
          <div className="setup-done-mark">
            <Sparkles size={28} />
          </div>
          <h2>Всё готово</h2>
          <p className="muted">Ждём соединение с backend.</p>
        </header>
        <div className="empty-state">Backend starting...</div>
      </div>
    );
  }

  if (profile.isError && isNetworkFetchError(profile.error)) {
    return (
      <div className="setup-step-body">
        <header className="setup-step-head">
          <div className="setup-done-mark">
            <Sparkles size={28} />
          </div>
          <h2>Всё готово</h2>
          <p className="muted">Ждём соединение с backend.</p>
        </header>
        <div className="empty-state">Backend starting...</div>
      </div>
    );
  }

  return (
    <div className="setup-step-body setup-done">
      <header className="setup-step-head">
        <div className="setup-done-mark">
          <Sparkles size={28} />
        </div>
        <h2>Всё готово</h2>
        <p className="muted">
          Профили сохранены, frpc установлен, сервер настроен. Можно запускать.
        </p>
      </header>

      <div className="setup-summary">
        <div>
          <span className="eyebrow">Адрес для друзей</span>
          <div className="setup-summary-address">
            <strong>{address ?? "—"}</strong>
            {address && (
              <button
                type="button"
                className="ghost-btn"
                onClick={() => navigator.clipboard.writeText(address)}
              >
                <Copy size={14} /> копировать
              </button>
            )}
          </div>
        </div>
        <div>
          <span className="eyebrow">MOTD</span>
          <strong>{profile.data?.minecraft.motd || "—"}</strong>
        </div>
        <div>
          <span className="eyebrow">Slots</span>
          <strong>{profile.data?.minecraft.max_players ?? 20}</strong>
        </div>
      </div>

      <div className="setup-action-row">
        <Button
          variant="primary"
          icon={<Play size={16} />}
          disabled={launch.isPending}
          onClick={() => launch.mutate()}
        >
          Запустить сейчас
        </Button>
        <Button onClick={() => setActiveScreen("home")}>Перейти на Home</Button>
      </div>

      {launch.error && (
        <div className="home-flash is-error">{(launch.error as Error).message}</div>
      )}
    </div>
  );
}

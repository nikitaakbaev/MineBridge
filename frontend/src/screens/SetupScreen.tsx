import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { DoneStep } from "../components/setup/DoneStep";
import { ServerStep } from "../components/setup/ServerStep";
import { StepNav } from "../components/setup/StepNav";
import { TunnelStep } from "../components/setup/TunnelStep";
import { VpsStep } from "../components/setup/VpsStep";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { api } from "../lib/api";
import type { SetupStep } from "../lib/types";
import { useAppStore } from "../store/app-store";

const STEP_ORDER: SetupStep[] = ["vps", "tunnel", "server", "done"];

export function SetupScreen() {
  const queryClient = useQueryClient();
  const setupStatus = useAppStore((state) => state.setupStatus);
  const setSetupStatus = useAppStore((state) => state.setSetupStatus);
  const [active, setActive] = useState<SetupStep>(setupStatus?.current_step ?? "vps");

  useEffect(() => {
    if (setupStatus?.current_step) setActive(setupStatus.current_step);
  }, [setupStatus?.current_step]);

  const advanceTo = async (step: SetupStep) => {
    setActive(step);
    const next = await api.setSetupStatus({ current_step: step });
    setSetupStatus(next);
    queryClient.invalidateQueries({ queryKey: ["setup-status"] });
  };

  const furthest =
    setupStatus?.current_step && STEP_ORDER.indexOf(setupStatus.current_step) >= STEP_ORDER.indexOf(active)
      ? setupStatus.current_step
      : active;

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Wizard"
        title="Настройка MineBridge"
        description="Линейный мастер первого запуска: VPS → туннель → сервер → запуск."
      />
      <StepNav current={active} furthest={furthest} onSelect={(step) => setActive(step)} />

      {active === "vps" && <VpsStep onAdvance={() => advanceTo("tunnel")} />}
      {active === "tunnel" && <TunnelStep onAdvance={() => advanceTo("server")} />}
      {active === "server" && <ServerStep onAdvance={() => advanceTo("done")} />}
      {active === "done" && <DoneStep />}
    </div>
  );
}

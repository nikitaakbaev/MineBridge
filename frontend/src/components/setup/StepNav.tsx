import { Check } from "lucide-react";

import type { SetupStep } from "../../lib/types";

type Step = {
  id: SetupStep;
  label: string;
  index: number;
};

const STEPS: Step[] = [
  { id: "vps", label: "VPS", index: 1 },
  { id: "tunnel", label: "Туннель", index: 2 },
  { id: "server", label: "Сервер", index: 3 },
  { id: "done", label: "Готово", index: 4 }
];

type StepNavProps = {
  current: SetupStep;
  furthest: SetupStep;
  onSelect: (step: SetupStep) => void;
};

export function StepNav({ current, furthest, onSelect }: StepNavProps) {
  const furthestIndex = STEPS.find((s) => s.id === furthest)?.index ?? 1;

  return (
    <ol className="setup-stepper">
      {STEPS.map((step) => {
        const isCurrent = step.id === current;
        const isDone = step.index < furthestIndex;
        const isReachable = step.index <= furthestIndex;
        const cls = ["setup-step"];
        if (isCurrent) cls.push("is-current");
        if (isDone) cls.push("is-done");
        if (!isReachable) cls.push("is-locked");

        return (
          <li key={step.id} className={cls.join(" ")}>
            <button
              type="button"
              disabled={!isReachable}
              onClick={() => isReachable && onSelect(step.id)}
            >
              <span className="setup-step-marker">
                {isDone ? <Check size={14} /> : step.index}
              </span>
              <span className="setup-step-label">{step.label}</span>
            </button>
          </li>
        );
      })}
    </ol>
  );
}

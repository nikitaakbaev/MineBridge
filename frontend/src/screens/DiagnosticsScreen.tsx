import { useMutation } from "@tanstack/react-query";
import { Activity, Wrench } from "lucide-react";

import { api } from "../lib/api";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { StatusBadge } from "../components/ui/StatusBadge";

export function DiagnosticsScreen() {
  const diagnostics = useMutation({ mutationFn: api.diagnostics });

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Diagnostics"
        title="Проверка готовности"
        description="Python backend проверяет Java, server.jar, EULA, FRP token, frpc, ports и VPS-поля."
        action={
          <Button
            variant="primary"
            icon={<Activity size={18} />}
            disabled={diagnostics.isPending}
            onClick={() => diagnostics.mutate()}
          >
            Запустить диагностику
          </Button>
        }
      />

      <Card title="Результаты" action={<Wrench size={16} />}>
        <div className="diagnostic-list">
          {(diagnostics.data || []).map((item) => (
            <div className="diagnostic-row" key={`${item.name}-${item.description}`}>
              <StatusBadge status={item.status} />
              <div>
                <strong>{item.name}</strong>
                <p>{item.description}</p>
              </div>
              {item.fix_available && <span className="fix-pill">fix: {item.fix_id}</span>}
            </div>
          ))}
          {!diagnostics.data && (
            <div className="empty-state">
              Нажмите кнопку диагностики, чтобы увидеть список проверок активных профилей.
            </div>
          )}
          {diagnostics.error && <div className="error-box">{String(diagnostics.error.message)}</div>}
        </div>
      </Card>
    </div>
  );
}

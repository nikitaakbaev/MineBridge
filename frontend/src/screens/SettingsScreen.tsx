import type { CSSProperties } from "react";
import { useEffect, useState } from "react";
import { RotateCcw, SwatchBook } from "lucide-react";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Field, TextInput } from "../components/ui/Field";
import { ScreenHeader } from "../components/ui/ScreenHeader";
import { DEFAULT_ACCENT_COLOR, normalizeHexColor } from "../lib/theme";
import { useAppStore } from "../store/app-store";

const accentSwatches = [
  { name: "Signal blue", value: "#4f8cff" },
  { name: "Relay green", value: "#45b36b" },
  { name: "Copper amber", value: "#d7a33d" },
  { name: "Port violet", value: "#8b7cf6" },
  { name: "Alert red", value: "#ef5f5f" },
  { name: "Graphite", value: "#a7b0ba" }
];

export function SettingsScreen() {
  const accentColor = useAppStore((state) => state.accentColor);
  const setAccentColor = useAppStore((state) => state.setAccentColor);
  const [customColor, setCustomColor] = useState(accentColor);

  useEffect(() => {
    setCustomColor(accentColor);
  }, [accentColor]);

  const onCustomColorChange = (value: string) => {
    setCustomColor(value);
    const normalized = normalizeHexColor(value);
    if (normalized) setAccentColor(normalized);
  };

  return (
    <div className="screen stack">
      <ScreenHeader
        eyebrow="Appearance"
        title="Настройки приложения"
        description="Выберите один акцентный цвет. Интерфейс использует его для действий, фокуса, графиков и терминала."
      />

      <div className="two-columns wide-left">
        <Card title="Акцентный цвет" className="appearance-card">
          <div className="accent-swatch-grid" aria-label="Готовые акцентные цвета">
            {accentSwatches.map((swatch) => (
              <button
                key={swatch.value}
                type="button"
                className={accentColor === swatch.value ? "accent-swatch is-active" : "accent-swatch"}
                style={{ "--swatch": swatch.value } as CSSProperties}
                onClick={() => setAccentColor(swatch.value)}
              >
                <span className="accent-swatch-color" />
                <span>{swatch.name}</span>
              </button>
            ))}
          </div>

          <div className="appearance-controls">
            <Field label="Custom color" hint="HEX, например #4f8cff">
              <TextInput
                type="color"
                value={accentColor}
                onChange={(event) => setAccentColor(event.target.value)}
                aria-label="Выбрать акцентный цвет"
              />
            </Field>
            <Field label="Current value">
              <TextInput value={customColor} onChange={(event) => onCustomColorChange(event.target.value)} />
            </Field>
            <Button
              icon={<RotateCcw size={15} />}
              variant="ghost"
              onClick={() => setAccentColor(DEFAULT_ACCENT_COLOR)}
            >
              Сбросить
            </Button>
          </div>
        </Card>

        <Card title="Preview" className="appearance-preview-card">
          <div className="appearance-preview-head">
            <SwatchBook size={22} />
            <div>
              <strong>MineBridge control</strong>
              <span>Акцент применяется сразу</span>
            </div>
          </div>
          <div className="appearance-preview-strip">
            <span />
            <span />
            <span />
          </div>
          <div className="appearance-preview-row">
            <Button variant="primary">Запустить сервер</Button>
            <span className="status-badge status-good">running</span>
          </div>
          <div className="appearance-preview-terminal">
            <span>&gt;</span> frpc connected
          </div>
        </Card>
      </div>
    </div>
  );
}

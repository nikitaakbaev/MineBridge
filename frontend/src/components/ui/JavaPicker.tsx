import type { JavaInstallation } from "../../lib/types";

type JavaPickerProps = {
  open: boolean;
  installations: JavaInstallation[];
  current?: string;
  onSelect: (installation: JavaInstallation) => void;
  onClose: () => void;
};

export function JavaPicker({ open, installations, current, onSelect, onClose }: JavaPickerProps) {
  if (!open) return null;
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <div>
            <h2>Найдено несколько Java</h2>
            <p className="muted">
              Выберите ту, которую использовать для запуска Minecraft-сервера.
            </p>
          </div>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>
        </header>
        <ul className="modal-list">
          {installations.length === 0 && (
            <li className="modal-empty">Java на этой машине не найдена.</li>
          )}
          {installations.map((item) => {
            const active = current && current === item.path;
            return (
              <li key={item.path}>
                <button
                  type="button"
                  className={`modal-list-item${active ? " is-active" : ""}`}
                  onClick={() => onSelect(item)}
                >
                  <div className="modal-list-title">
                    <span>Java {item.version || "?"}</span>
                    {item.vendor && <span className="modal-list-vendor">{item.vendor}</span>}
                  </div>
                  <div className="modal-list-path">{item.path}</div>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}

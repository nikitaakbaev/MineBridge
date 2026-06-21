import { useEffect, useRef, useState } from "react";

type OverflowMenuProps = {
  items: Array<{
    label: string;
    onClick: () => void;
    danger?: boolean;
    disabled?: boolean;
  }>;
  ariaLabel?: string;
};

export function OverflowMenu({ items, ariaLabel = "Меню действий" }: OverflowMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (event: MouseEvent) => {
      if (!ref.current) return;
      if (!ref.current.contains(event.target as Node)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("mousedown", handler);
    window.addEventListener("keydown", escape);
    return () => {
      window.removeEventListener("mousedown", handler);
      window.removeEventListener("keydown", escape);
    };
  }, [open]);

  return (
    <div className="overflow-menu" ref={ref}>
      <button
        type="button"
        className="overflow-trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={ariaLabel}
        onClick={() => setOpen((v) => !v)}
      >
        ⋮
      </button>
      {open && (
        <ul className="overflow-list" role="menu">
          {items.map((item, idx) => (
            <li key={idx} role="none">
              <button
                role="menuitem"
                type="button"
                className={`overflow-item${item.danger ? " is-danger" : ""}`}
                disabled={item.disabled}
                onClick={() => {
                  setOpen(false);
                  item.onClick();
                }}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

import { AnimatePresence, motion } from "framer-motion";
import { Terminal, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { useMutation } from "@tanstack/react-query";

import { api } from "../../lib/api";
import { useAppStore } from "../../store/app-store";
import { Console } from "./Console";

export function ConsoleDrawer() {
  const open = useAppStore((state) => state.consoleOpen);
  const setOpen = useAppStore((state) => state.setConsoleOpen);
  const minecraftLogs = useAppStore((state) => state.minecraftLogs);
  const minecraftStatus = useAppStore((state) => state.minecraftStatus);
  const hostRef = useRef<HTMLDivElement | null>(null);

  const send = useMutation({
    mutationFn: (command: string) => api.sendMinecraftCommand(command)
  });

  useEffect(() => {
    if (!open) return;
    // Give xterm time to mount before focusing it.
    const id = window.setTimeout(() => {
      const term = hostRef.current?.querySelector(".xterm-helper-textarea") as
        | HTMLTextAreaElement
        | null;
      term?.focus();
    }, 60);
    return () => window.clearTimeout(id);
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="console-drawer"
          initial={{ y: 280 }}
          animate={{ y: 0 }}
          exit={{ y: 280 }}
          transition={{ duration: 0.2 }}
          ref={hostRef}
          onMouseDown={() => {
            const term = hostRef.current?.querySelector(".xterm-helper-textarea") as
              | HTMLTextAreaElement
              | null;
            term?.focus();
          }}
        >
          <div className="console-drawer-header">
            <div className="console-drawer-title">
              <Terminal size={14} />
              <span>Консоль сервера</span>
              <kbd>~</kbd>
            </div>
            <button
              type="button"
              className="console-drawer-close"
              onClick={() => setOpen(false)}
              aria-label="Закрыть консоль"
            >
              <X size={16} />
            </button>
          </div>
          <Console
            lines={minecraftLogs.slice(-300)}
            onSubmit={(command) => send.mutate(command)}
            disabled={minecraftStatus !== "running"}
            disabledHint="запустите сервер, чтобы вводить команды"
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

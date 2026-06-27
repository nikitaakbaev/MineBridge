import { useEffect, useRef } from "react";
import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";

import { readCssVariable } from "../../lib/theme";

type TerminalConsoleProps = {
  lines: string[];
  title?: string;
};

export function TerminalConsole({ lines, title }: TerminalConsoleProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const terminalRef = useRef<Terminal | null>(null);

  useEffect(() => {
    if (!hostRef.current || terminalRef.current) return;
    const terminal = new Terminal({
      convertEol: true,
      cursorBlink: false,
      fontFamily: "JetBrains Mono, ui-monospace, SFMono-Regular, monospace",
      fontSize: 13,
      theme: {
        background: readCssVariable("--surface-sunken", "#07090b"),
        foreground: readCssVariable("--text-soft", "#b8c0c8"),
        cursor: readCssVariable("--accent", "#4f8cff")
      }
    });
    const fit = new FitAddon();
    terminal.loadAddon(fit);
    terminal.open(hostRef.current);
    terminalRef.current = terminal;
    window.requestAnimationFrame(() => fit.fit());

    let frame = 0;
    const observer = new ResizeObserver(() => {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(() => fit.fit());
    });
    observer.observe(hostRef.current);

    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
      terminal.dispose();
      terminalRef.current = null;
    };
  }, []);

  useEffect(() => {
    const terminal = terminalRef.current;
    if (!terminal) return;
    terminal.clear();
    for (const line of lines.slice(-250)) {
      terminal.writeln(line);
    }
  }, [lines]);

  return (
    <div className="terminal-card">
      {title && <div className="terminal-title">{title}</div>}
      <div className="terminal-host" ref={hostRef} />
    </div>
  );
}

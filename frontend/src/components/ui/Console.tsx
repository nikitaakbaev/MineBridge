import { useEffect, useRef } from "react";
import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";

type ConsoleProps = {
  lines: string[];
  title?: string;
  prompt?: string;
  /** When provided the console becomes interactive and submits typed commands. */
  onSubmit?: (command: string) => void;
  disabled?: boolean;
  disabledHint?: string;
};

const COLORS = {
  prompt: "\u001b[38;5;45m",
  dim: "\u001b[38;5;245m",
  reset: "\u001b[0m"
};

export function Console({
  lines,
  title,
  prompt = "> ",
  onSubmit,
  disabled = false,
  disabledHint
}: ConsoleProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const terminalRef = useRef<Terminal | null>(null);
  const fitRef = useRef<FitAddon | null>(null);
  const writtenRef = useRef(0);
  const lastLineRef = useRef<string | null>(null);
  const bufferRef = useRef("");
  const historyRef = useRef<string[]>([]);
  const historyIndexRef = useRef<number | null>(null);

  // Keep the latest callbacks/flags accessible inside the stable onData handler.
  const onSubmitRef = useRef(onSubmit);
  const disabledRef = useRef(disabled);
  onSubmitRef.current = onSubmit;
  disabledRef.current = disabled;

  const interactive = Boolean(onSubmit);

  useEffect(() => {
    if (!hostRef.current || terminalRef.current) return;
    const terminal = new Terminal({
      convertEol: true,
      cursorBlink: interactive,
      disableStdin: !interactive,
      fontFamily: "JetBrains Mono, ui-monospace, SFMono-Regular, monospace",
      fontSize: 13,
      theme: {
        background: "#060d18",
        foreground: "#d7e0ee",
        cursor: "#7dd3fc",
        selectionBackground: "#1e3a5f"
      }
    });
    const fit = new FitAddon();
    terminal.loadAddon(fit);
    terminal.open(hostRef.current);
    terminalRef.current = terminal;
    fitRef.current = fit;
    window.requestAnimationFrame(() => fit.fit());

    let frame = 0;
    const observer = new ResizeObserver(() => {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(() => fit.fit());
    });
    observer.observe(hostRef.current);

    const writePrompt = () => {
      if (!interactive) return;
      terminal.write(`\r\u001b[2K${COLORS.prompt}${prompt}${COLORS.reset}${bufferRef.current}`);
    };

    const replaceBuffer = (next: string) => {
      bufferRef.current = next;
      writePrompt();
    };

    if (interactive) {
      terminal.onData((data) => {
        if (disabledRef.current) return;
        switch (data) {
          case "\r": {
            const command = bufferRef.current.trim();
            terminal.write("\r\n");
            bufferRef.current = "";
            historyIndexRef.current = null;
            if (command) {
              historyRef.current.push(command);
              onSubmitRef.current?.(command);
            }
            writePrompt();
            break;
          }
          case "\u007f": // Backspace
            if (bufferRef.current.length > 0) {
              bufferRef.current = bufferRef.current.slice(0, -1);
              terminal.write("\b \b");
            }
            break;
          case "\u0003": // Ctrl+C
            bufferRef.current = "";
            terminal.write("^C\r\n");
            writePrompt();
            break;
          case "\u001b[A": { // Up
            const history = historyRef.current;
            if (history.length === 0) break;
            const index =
              historyIndexRef.current === null
                ? history.length - 1
                : Math.max(0, historyIndexRef.current - 1);
            historyIndexRef.current = index;
            replaceBuffer(history[index]);
            break;
          }
          case "\u001b[B": { // Down
            const history = historyRef.current;
            if (historyIndexRef.current === null) break;
            const index = historyIndexRef.current + 1;
            if (index >= history.length) {
              historyIndexRef.current = null;
              replaceBuffer("");
            } else {
              historyIndexRef.current = index;
              replaceBuffer(history[index]);
            }
            break;
          }
          default:
            if (data >= " " || data === "\t") {
              bufferRef.current += data;
              terminal.write(data);
            }
        }
      });
      writePrompt();
    }

    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
      terminal.dispose();
      terminalRef.current = null;
      fitRef.current = null;
      writtenRef.current = 0;
      lastLineRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Stream output lines incrementally so the typed prompt is preserved.
  useEffect(() => {
    const terminal = terminalRef.current;
    if (!terminal) return;

    const writePrompt = () => {
      if (!interactive) return;
      terminal.write(`\r\u001b[2K${COLORS.prompt}${prompt}${COLORS.reset}${bufferRef.current}`);
    };

    let newLines: string[];
    const lastLine = lines.length > 0 ? lines[lines.length - 1] : null;
    if (lines.length < writtenRef.current) {
      // The buffer shrank (reset) — repaint everything.
      terminal.clear();
      newLines = lines;
    } else if (lines.length === writtenRef.current) {
      // Length unchanged: either nothing new, or a capped ring-buffer shift.
      if (lastLine === lastLineRef.current) {
        return;
      }
      terminal.clear();
      newLines = lines;
    } else {
      newLines = lines.slice(writtenRef.current);
    }
    writtenRef.current = lines.length;
    lastLineRef.current = lastLine;

    if (newLines.length === 0) return;

    // Erase the current prompt line, append output, then redraw the prompt.
    if (interactive) terminal.write("\r\u001b[2K");
    for (const line of newLines) {
      terminal.writeln(line);
    }
    writePrompt();
  }, [lines, interactive, prompt]);

  return (
    <div className="terminal-card">
      {title && (
        <div className="terminal-title">
          <span>{title}</span>
          {interactive && (
            <span className="terminal-hint">
              {disabled ? disabledHint || "консоль недоступна" : "введите команду и нажмите Enter"}
            </span>
          )}
        </div>
      )}
      <div className="terminal-host" ref={hostRef} />
    </div>
  );
}

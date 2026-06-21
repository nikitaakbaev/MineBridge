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

const ESC = "";
const COLORS = {
  prompt: `${ESC}[38;5;45m`,
  dim: `${ESC}[38;5;245m`,
  reset: `${ESC}[0m`
};
const ERASE_LINE = `\r${ESC}[2K`;

const KEY_BACKSPACE = "";
const KEY_CTRL_C = "";
const KEY_UP = `${ESC}[A`;
const KEY_DOWN = `${ESC}[B`;

function commonPrefixLength(a: string[], b: string[]): number {
  const max = Math.min(a.length, b.length);
  let i = 0;
  while (i < max && a[i] === b[i]) i++;
  return i;
}

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
  const renderedRef = useRef<string[]>([]);
  const bufferRef = useRef("");
  const historyRef = useRef<string[]>([]);
  const historyIndexRef = useRef<number | null>(null);

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
      scrollback: 5000,
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
      terminal.write(`${ERASE_LINE}${COLORS.prompt}${prompt}${COLORS.reset}${bufferRef.current}`);
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
          case KEY_BACKSPACE:
            if (bufferRef.current.length > 0) {
              bufferRef.current = bufferRef.current.slice(0, -1);
              terminal.write("\b \b");
            }
            break;
          case KEY_CTRL_C:
            bufferRef.current = "";
            terminal.write("^C\r\n");
            writePrompt();
            break;
          case KEY_UP: {
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
          case KEY_DOWN: {
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
      renderedRef.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const terminal = terminalRef.current;
    if (!terminal) return;

    const writePrompt = () => {
      if (!interactive) return;
      terminal.write(`${ERASE_LINE}${COLORS.prompt}${prompt}${COLORS.reset}${bufferRef.current}`);
    };

    const previous = renderedRef.current;
    const sharedPrefix = commonPrefixLength(previous, lines);
    const previousMatchesPrefix = sharedPrefix === previous.length;

    let newLines: string[];
    if (previousMatchesPrefix) {
      newLines = lines.slice(previous.length);
    } else {
      terminal.reset();
      newLines = lines;
    }
    renderedRef.current = lines.slice();

    if (newLines.length === 0) {
      if (!previousMatchesPrefix) writePrompt();
      return;
    }

    if (interactive) terminal.write(ERASE_LINE);
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

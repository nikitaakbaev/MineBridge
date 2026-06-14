import { useEffect, useState } from "react";

/** Format a duration in seconds as `1ч 02м 03с`. */
export function formatDuration(totalSeconds: number): string {
  if (!totalSeconds || totalSeconds < 0) return "—";
  const seconds = Math.floor(totalSeconds % 60);
  const minutes = Math.floor((totalSeconds / 60) % 60);
  const hours = Math.floor(totalSeconds / 3600);
  const pad = (value: number) => value.toString().padStart(2, "0");
  if (hours > 0) return `${hours}ч ${pad(minutes)}м`;
  if (minutes > 0) return `${minutes}м ${pad(seconds)}с`;
  return `${seconds}с`;
}

/** Live uptime in seconds derived from a start timestamp (ms). */
export function useUptime(startedAt: number | null): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (startedAt === null) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [startedAt]);
  if (startedAt === null) return 0;
  return Math.max(0, (now - startedAt) / 1000);
}

export function formatMb(mb: number): string {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} ГБ`;
  return `${Math.round(mb)} МБ`;
}

import { useEffect } from "react";

import { WS_URL } from "../lib/api";
import type { BackendEvent } from "../lib/types";
import { useAppStore } from "../store/app-store";

export function useBackendEvents() {
  const ingestEvent = useAppStore((state) => state.ingestEvent);
  const setBackendConnected = useAppStore((state) => state.setBackendConnected);

  useEffect(() => {
    let closed = false;
    let socket: WebSocket | null = null;
    let timer: number | null = null;

    const connect = () => {
      socket = new WebSocket(WS_URL);
      socket.onopen = () => setBackendConnected(true);
      socket.onclose = () => {
        setBackendConnected(false);
        if (!closed) {
          timer = window.setTimeout(connect, 1400);
        }
      };
      socket.onerror = () => setBackendConnected(false);
      socket.onmessage = (message) => {
        try {
          ingestEvent(JSON.parse(message.data) as BackendEvent);
        } catch {
          // Ignore malformed local events.
        }
      };
    };

    connect();

    return () => {
      closed = true;
      if (timer) window.clearTimeout(timer);
      socket?.close();
    };
  }, [ingestEvent, setBackendConnected]);
}

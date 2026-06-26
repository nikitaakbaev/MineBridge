import { useEffect } from "react";

import { api, wsUrl } from "../lib/api";
import type { BackendEvent } from "../lib/types";
import { useAppStore } from "../store/app-store";

export function useBackendEvents() {
  const ingestEvent = useAppStore((state) => state.ingestEvent);
  const setBackendConnected = useAppStore((state) => state.setBackendConnected);
  const hydrateState = useAppStore((state) => state.hydrateState);

  useEffect(() => {
    let closed = false;
    let socket: WebSocket | null = null;
    let timer: number | null = null;

    const hydrate = () => {
      api
        .runtimeState()
        .then((state) => {
          if (!closed) hydrateState(state);
        })
        .catch(() => {
          /* backend not ready yet; the websocket will retry */
        });
    };

    const connect = () => {
      socket = new WebSocket(wsUrl());
      socket.onopen = () => {
        setBackendConnected(true);
        hydrate();
      };
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
  }, [ingestEvent, setBackendConnected, hydrateState]);
}

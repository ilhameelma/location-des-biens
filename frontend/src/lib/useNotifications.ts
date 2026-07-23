// Étape 9 — Notifications
// Charge l'historique des notifications de l'utilisateur connecté et les
// tient à jour en temps réel via le canal WebSocket privé
// (/api/notifications/ws) ouvert pour toute la durée de la session.
import { useEffect, useRef, useState } from "react";
import { api, wsUrl } from "./api";
import { useAuth } from "./auth";
import type { Notification } from "../types";

export function useNotifications() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!user) return;

    setLoading(true);
    api
      .get<Notification[]>("/notifications/me")
      .then(setNotifications)
      .finally(() => setLoading(false));

    const socket = new WebSocket(wsUrl("/notifications/ws"));
    socketRef.current = socket;
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data?.type === "notification") {
          const { type: _t, ...notif } = data;
          setNotifications((prev) => [notif as Notification, ...prev]);
        }
      } catch {
        // trame non-JSON ignorée
      }
    };

    return () => {
      socket.close();
      socketRef.current = null;
    };
  }, [user?.id]);

  const unreadCount = notifications.filter((n) => !n.lu).length;

  const markRead = async (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, lu: true } : n)));
    try {
      await api.patch(`/notifications/${id}/lue`);
    } catch {
      // best-effort : l'état local reste à jour même si la requête échoue
    }
  };

  const markAllRead = async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, lu: true })));
    try {
      await api.patch("/notifications/me/tout-lire");
    } catch {
      // best-effort
    }
  };

  return { notifications, unreadCount, loading, markRead, markAllRead };
}

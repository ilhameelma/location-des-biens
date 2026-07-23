// Étape 8 — Messagerie temps réel (WebSocket)
// Hook partagé entre l'espace client et l'espace propriétaire : ouvre une
// connexion WebSocket sur la conversation sélectionnée, pousse les nouveaux
// messages reçus au fur et à mesure, et expose une fonction d'envoi.
import { useEffect, useRef, useState } from "react";
import { wsUrl } from "./api";
import type { Message } from "../types";

export function useConversationSocket(
  conversationId: string | null,
  onMessage: (message: Message) => void
) {
  const wsRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  const [connected, setConnected] = useState(false);

  // Toujours appeler la dernière version du callback, sans pour autant
  // recréer la connexion WebSocket à chaque re-render du composant parent.
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    if (!conversationId) {
      setConnected(false);
      return;
    }

    const socket = new WebSocket(wsUrl(`/conversations/ws/${conversationId}`));
    wsRef.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data?.type === "message") {
          onMessageRef.current(data as Message);
        }
      } catch {
        // Trame non-JSON ignorée
      }
    };

    return () => {
      socket.close();
      wsRef.current = null;
      setConnected(false);
    };
  }, [conversationId]);

  const sendMessage = (contenu: string): boolean => {
    const socket = wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ contenu }));
      return true;
    }
    return false;
  };

  return { connected, sendMessage };
}

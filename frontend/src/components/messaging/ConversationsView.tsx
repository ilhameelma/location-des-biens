// Étape 8 — Messagerie temps réel
// Composant partagé entre l'espace client et l'espace propriétaire :
// liste des conversations à gauche, fil de discussion temps réel à droite.
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { MessageSquare, Send, Loader2 } from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { useConversationSocket } from "../../lib/useConversationSocket";
import type { Conversation, Message } from "../../types";

function formatHeure(iso: string) {
  return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

function formatApercu(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(iso);
  const auj = new Date();
  const memeJour = d.toDateString() === auj.toDateString();
  return memeJour
    ? formatHeure(iso)
    : d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });
}

export default function ConversationsView() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedId, setSelectedId] = useState<string | null>(searchParams.get("conv"));
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [input, setInput] = useState("");

  const scrollRef = useRef<HTMLDivElement>(null);
  const knownIds = useRef<Set<string>>(new Set());

  const loadConversations = () => {
    setLoadingConvs(true);
    api
      .get<Conversation[]>("/conversations")
      .then((data) => {
        setConversations(data);
        // Si aucune conversation sélectionnée mais qu'on en a une dispo, ouvrir la première.
        setSelectedId((current) => current ?? data[0]?.id ?? null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoadingConvs(false));
  };

  useEffect(loadConversations, []);

  useEffect(() => {
    if (!selectedId) {
      setMessages([]);
      return;
    }
    setLoadingMessages(true);
    setSearchParams((p) => {
      const next = new URLSearchParams(p);
      next.set("conv", selectedId);
      return next;
    });
    api
      .get<Message[]>(`/conversations/${selectedId}/messages`)
      .then((data) => {
        knownIds.current = new Set(data.map((m) => m.id));
        setMessages(data);
        // La conversation vient d'être ouverte -> ses messages sont marqués lus côté back-end.
        setConversations((prev) =>
          prev.map((c) => (c.id === selectedId ? { ...c, non_lus: 0 } : c))
        );
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoadingMessages(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleIncoming = (message: Message) => {
    if (message.conversation_id !== selectedId) return;
    if (knownIds.current.has(message.id)) return;
    knownIds.current.add(message.id);
    setMessages((prev) => [...prev, message]);
    setConversations((prev) =>
      prev.map((c) =>
        c.id === message.conversation_id
          ? { ...c, dernier_message: message.contenu, date_dernier_message: message.date_envoi }
          : c
      )
    );
  };

  const { connected, sendMessage } = useConversationSocket(selectedId, handleIncoming);

  const handleSend = async () => {
    const contenu = input.trim();
    if (!contenu || !selectedId) return;
    setInput("");

    const sentViaSocket = sendMessage(contenu);
    if (sentViaSocket) return; // la confirmation arrivera par le canal WebSocket (écho serveur)

    // Repli REST si le WebSocket n'est pas connecté (ex: reconnexion en cours)
    try {
      const message = await api.post<Message>(`/conversations/${selectedId}/messages`, { contenu });
      if (!knownIds.current.has(message.id)) {
        knownIds.current.add(message.id);
        setMessages((prev) => [...prev, message]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d'envoyer le message");
    }
  };

  const selectedConv = useMemo(
    () => conversations.find((c) => c.id === selectedId) ?? null,
    [conversations, selectedId]
  );

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Messagerie</h1>
        {selectedId && (
          <span
            className={`flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide ${
              connected ? "text-[var(--color-sage)]" : "text-[var(--color-ink-3)]"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                connected ? "bg-[var(--color-sage)]" : "bg-[var(--color-ink-3)]"
              }`}
            />
            {connected ? "Connecté" : "Connexion…"}
          </span>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}

      <div className="mt-6 flex h-[560px] overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)]">
        {/* Liste des conversations */}
        <div className="w-72 shrink-0 overflow-y-auto border-r border-[var(--color-line)] p-3">
          {loadingConvs ? (
            <div className="flex items-center justify-center gap-2 py-8 text-sm text-[var(--color-ink-3)]">
              <Loader2 size={16} className="animate-spin" /> Chargement…
            </div>
          ) : conversations.length === 0 ? (
            <p className="p-3 text-sm text-[var(--color-ink-3)]">Aucune conversation pour le moment.</p>
          ) : (
            <div className="space-y-1.5">
              {conversations.map((c) => (
                <button
                  key={c.id}
                  onClick={() => setSelectedId(c.id)}
                  className={`w-full rounded-md p-3 text-left transition-colors ${
                    c.id === selectedId
                      ? "bg-[var(--color-brass)]/10 ring-1 ring-[var(--color-brass)]"
                      : "hover:bg-[var(--color-paper-2)]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-medium text-[var(--color-ink)]">
                      {c.autre_prenom} {c.autre_nom}
                    </span>
                    <div className="flex items-center gap-1.5">
                      {c.date_dernier_message && (
                        <span className="shrink-0 font-mono text-[10px] text-[var(--color-ink-3)]">
                          {formatApercu(c.date_dernier_message)}
                        </span>
                      )}
                      {c.non_lus > 0 && (
                        <span className="flex h-4 min-w-4 shrink-0 items-center justify-center rounded-full bg-[var(--color-brass)] px-1 text-[10px] font-semibold text-white">
                          {c.non_lus}
                        </span>
                      )}
                    </div>
                  </div>
                  {c.bien_titre && (
                    <div className="truncate text-[11px] text-[var(--color-brass-deep)]">
                      {c.bien_titre}
                    </div>
                  )}
                  <div className="truncate text-xs text-[var(--color-ink-3)]">
                    {c.dernier_message ?? "Aucun message"}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Fil de discussion */}
        <div className="flex flex-1 flex-col">
          {!selectedId || !selectedConv ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 text-[var(--color-ink-3)]">
              <MessageSquare size={28} />
              <p className="max-w-xs text-center text-sm">
                Sélectionnez une conversation pour afficher les messages.
              </p>
            </div>
          ) : (
            <>
              <div className="border-b border-[var(--color-line)] px-4 py-3">
                <div className="text-sm font-medium text-[var(--color-ink)]">
                  {selectedConv.autre_prenom} {selectedConv.autre_nom}
                </div>
                {selectedConv.bien_titre && (
                  <div className="text-xs text-[var(--color-ink-3)]">À propos de « {selectedConv.bien_titre} »</div>
                )}
              </div>

              <div ref={scrollRef} className="flex-1 space-y-2 overflow-y-auto p-4">
                {loadingMessages ? (
                  <div className="flex items-center justify-center gap-2 py-8 text-sm text-[var(--color-ink-3)]">
                    <Loader2 size={16} className="animate-spin" /> Chargement…
                  </div>
                ) : messages.length === 0 ? (
                  <p className="py-8 text-center text-sm text-[var(--color-ink-3)]">
                    Aucun message. Écrivez le premier !
                  </p>
                ) : (
                  messages.map((m) => {
                    const mine = m.expediteur_id === user?.id;
                    return (
                      <div key={m.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}>
                        <div
                          className={`max-w-[70%] rounded-lg px-3 py-2 text-sm ${
                            mine
                              ? "bg-[var(--color-brass)] text-white"
                              : "bg-[var(--color-paper-2)] text-[var(--color-ink)]"
                          }`}
                        >
                          <div className="whitespace-pre-wrap break-words">{m.contenu}</div>
                          <div
                            className={`mt-1 text-right font-mono text-[10px] ${
                              mine ? "text-white/70" : "text-[var(--color-ink-3)]"
                            }`}
                          >
                            {formatHeure(m.date_envoi)}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              <div className="flex items-center gap-2 border-t border-[var(--color-line)] p-3">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Écrire un message…"
                  className="flex-1 rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim()}
                  className="rounded-md bg-[var(--color-brass)] p-2 text-white transition-colors hover:bg-[var(--color-brass-deep)] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Send size={16} />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

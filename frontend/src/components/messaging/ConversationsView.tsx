// Étape 8 — Messagerie temps réel
// Composant partagé entre l'espace client et l'espace propriétaire :
// liste des conversations à gauche, fil de discussion temps réel à droite.
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { MessageSquare, Send, Loader2, Star, Paperclip, FileText, ArrowLeft } from "lucide-react";
import { api, API_BASE_URL, formatErrorDetail } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { useConversationSocket } from "../../lib/useConversationSocket";
import type { Avis, Conversation, Message } from "../../types";
import StarRating from "../ui/StarRating";

// Types acceptés côté sélecteur de fichier — doit rester cohérent avec
// TYPES_PIECE_JOINTE_AUTORISES côté back-end (routers/messagerie.py).
const ACCEPT_PIECE_JOINTE = "image/jpeg,image/png,image/webp,image/gif,application/pdf";
const TAILLE_MAX_PIECE_JOINTE = 10 * 1024 * 1024; // 10 Mo — doit matcher le back-end

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

  // --- Pièces jointes (photo / PDF) ---
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [attachmentError, setAttachmentError] = useState<string | null>(null);

  // --- Avis laissé en fin de conversation (client uniquement) ---
  // bien_id -> avis déjà laissé par le client connecté sur ce bien, pour ne
  // pas proposer deux fois le formulaire (le back-end n'empêche pas les
  // doublons, donc ce garde-fou est côté front).
  const [mesAvisParBien, setMesAvisParBien] = useState<Record<string, Avis>>({});
  const [avisOuvert, setAvisOuvert] = useState(false);
  const [avisNote, setAvisNote] = useState(0);
  const [avisCommentaire, setAvisCommentaire] = useState("");
  const [avisSubmitting, setAvisSubmitting] = useState(false);
  const [avisError, setAvisError] = useState<string | null>(null);

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

  // Le client charge une seule fois la liste de ses avis déjà laissés, pour
  // savoir sur quels biens le formulaire ne doit plus être proposé.
  // Inutile (et interdit, 403) côté propriétaire — /avis/me est réservé au rôle client.
  useEffect(() => {
    if (user?.role !== "client") return;
    api
      .get<Avis[]>("/avis/me")
      .then((liste) => {
        const map: Record<string, Avis> = {};
        liste.forEach((a) => {
          map[a.bien_id] = a;
        });
        setMesAvisParBien(map);
      })
      .catch(() => {
        /* pas bloquant : le panneau avis reste juste proposé même si déjà laissé */
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.role]);

  // Referme le panneau avis en changeant de conversation, pour ne pas laisser
  // un formulaire ouvert/rempli associé à la mauvaise annonce.
  useEffect(() => {
    setAvisOuvert(false);
    setAvisNote(0);
    setAvisCommentaire("");
    setAvisError(null);
  }, [selectedId]);

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

  // Envoi d'une pièce jointe (photo ou PDF) — toujours en REST (multipart),
  // le WebSocket ne portant que du JSON texte. Le message créé est ajouté
  // directement à l'état local (comme le repli REST du texte ci-dessus) ;
  // l'écho reçu ensuite via le WebSocket est dédupliqué par `knownIds`.
  const handleSendFile = async (file: File) => {
    if (!selectedId) return;
    setAttachmentError(null);

    if (file.size > TAILLE_MAX_PIECE_JOINTE) {
      setAttachmentError("Fichier trop volumineux (10 Mo maximum).");
      return;
    }

    setUploadingFile(true);
    try {
      const formData = new FormData();
      formData.append("fichier", file);

      const res = await fetch(`${API_BASE_URL}/conversations/${selectedId}/messages/fichier`, {
        method: "POST",
        credentials: "include", // envoie le cookie httpOnly, comme les autres requêtes
        body: formData,
        // Pas de Content-Type ici — le navigateur le génère avec le boundary du FormData
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(formatErrorDetail(body.detail, res.status) || `Erreur upload (${res.status})`);
      }

      const message: Message = await res.json();
      if (!knownIds.current.has(message.id)) {
        knownIds.current.add(message.id);
        setMessages((prev) => [...prev, message]);
      }
      setConversations((prev) =>
        prev.map((c) =>
          c.id === selectedId
            ? {
                ...c,
                dernier_message: message.piece_jointe_type === "pdf" ? "📄 Document PDF" : "📷 Photo",
                date_dernier_message: message.date_envoi,
              }
            : c
        )
      );
    } catch (err) {
      setAttachmentError(err instanceof Error ? err.message : "Impossible d'envoyer le fichier");
    } finally {
      setUploadingFile(false);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ""; // permet de resélectionner le même fichier ensuite
    if (file) handleSendFile(file);
  };

  const selectedConv = useMemo(
    () => conversations.find((c) => c.id === selectedId) ?? null,
    [conversations, selectedId]
  );

  const soumettreAvis = async () => {
    if (!selectedConv?.bien_id) return;
    if (avisNote === 0) {
      setAvisError("Choisis une note avant d'envoyer ton avis.");
      return;
    }
    setAvisSubmitting(true);
    setAvisError(null);
    try {
      const avis = await api.post<Avis>("/avis", {
        proprietaire_id: selectedConv.proprietaire_id,
        bien_id: selectedConv.bien_id,
        note: avisNote,
        commentaire: avisCommentaire.trim() || undefined,
      });
      setMesAvisParBien((prev) => ({ ...prev, [avis.bien_id]: avis }));
      setAvisOuvert(false);
    } catch (err) {
      setAvisError(err instanceof Error ? err.message : "Impossible d'envoyer l'avis");
    } finally {
      setAvisSubmitting(false);
    }
  };

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

      <div className="mt-6 flex h-[70vh] max-h-[560px] overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] md:h-[560px]">
        {/* Liste des conversations — pleine largeur sur mobile tant qu'aucune
            conversation n'est sélectionnée, masquée dès qu'on ouvre un fil ;
            toujours visible côte à côte à partir de md */}
        <div
          className={`w-full shrink-0 overflow-y-auto border-r border-[var(--color-line)] p-3 md:flex md:w-72 ${
            selectedId ? "hidden md:block" : "block"
          }`}
        >
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

        {/* Fil de discussion — masqué sur mobile tant qu'aucune conversation
            n'est sélectionnée (pour ne pas écraser la liste), toujours
            visible à partir de md */}
        <div className={`flex-1 flex-col md:flex ${selectedId ? "flex" : "hidden md:flex"}`}>
          {!selectedId || !selectedConv ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 text-[var(--color-ink-3)]">
              <MessageSquare size={28} />
              <p className="max-w-xs text-center text-sm">
                Sélectionnez une conversation pour afficher les messages.
              </p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2 border-b border-[var(--color-line)] px-4 py-3">
                <button
                  type="button"
                  onClick={() => setSelectedId(null)}
                  className="-ml-1 rounded-md p-1 text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)] md:hidden"
                  aria-label="Retour à la liste des conversations"
                >
                  <ArrowLeft size={18} />
                </button>
                <div>
                  <div className="text-sm font-medium text-[var(--color-ink)]">
                    {selectedConv.autre_prenom} {selectedConv.autre_nom}
                  </div>
                  {selectedConv.bien_titre && (
                    <div className="text-xs text-[var(--color-ink-3)]">À propos de « {selectedConv.bien_titre} »</div>
                  )}
                </div>
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
                          {m.piece_jointe_url && m.piece_jointe_type === "image" && (
                            <a
                              href={m.piece_jointe_url}
                              target="_blank"
                              rel="noreferrer"
                              className={m.contenu ? "mb-2 block" : "block"}
                            >
                              <img
                                src={m.piece_jointe_url}
                                alt={m.piece_jointe_nom ?? "Photo envoyée"}
                                className="max-h-56 w-full rounded-md object-cover"
                              />
                            </a>
                          )}
                          {m.piece_jointe_url && m.piece_jointe_type === "pdf" && (
                            <a
                              href={m.piece_jointe_url}
                              target="_blank"
                              rel="noreferrer"
                              className={`flex items-center gap-2 rounded-md border px-2.5 py-2 text-xs font-medium transition-colors ${
                                m.contenu ? "mb-2" : ""
                              } ${
                                mine
                                  ? "border-white/30 hover:bg-white/10"
                                  : "border-[var(--color-line)] hover:bg-white"
                              }`}
                            >
                              <FileText size={16} className="shrink-0" />
                              <span className="truncate">{m.piece_jointe_nom ?? "Document PDF"}</span>
                            </a>
                          )}
                          {m.contenu && <div className="whitespace-pre-wrap break-words">{m.contenu}</div>}
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

              {/* Avis sur le propriétaire — visible côté client uniquement, et
                  seulement si la conversation est rattachée à une annonce
                  (l'avis exige un bien_id côté back-end). */}
              {user?.role === "client" && selectedConv.bien_id && (
                <div className="border-t border-[var(--color-line)] bg-[var(--color-paper)] px-4 py-3">
                  {mesAvisParBien[selectedConv.bien_id] ? (
                    <div className="flex items-center gap-2 text-xs text-[var(--color-ink-3)]">
                      <Star size={13} className="fill-[var(--color-brass)] text-[var(--color-brass)]" />
                      Avis déjà laissé sur ce propriétaire pour «&nbsp;{selectedConv.bien_titre}&nbsp;» —
                      <StarRating value={mesAvisParBien[selectedConv.bien_id].note} size={13} />
                    </div>
                  ) : !avisOuvert ? (
                    <button
                      type="button"
                      onClick={() => setAvisOuvert(true)}
                      className="flex items-center gap-1.5 text-xs font-medium text-[var(--color-brass-deep)] hover:underline"
                    >
                      <Star size={13} />
                      Donner mon avis sur ce propriétaire
                    </button>
                  ) : (
                    <div>
                      <p className="mb-2 text-xs font-medium text-[var(--color-ink-2)]">
                        Votre avis sur {selectedConv.autre_prenom} {selectedConv.autre_nom} — «&nbsp;
                        {selectedConv.bien_titre}&nbsp;»
                      </p>
                      <StarRating value={avisNote} onChange={setAvisNote} size={20} />
                      <textarea
                        value={avisCommentaire}
                        onChange={(e) => setAvisCommentaire(e.target.value)}
                        rows={2}
                        placeholder="Commentaire (optionnel)…"
                        className="mt-2 w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                      />
                      {avisError && <p className="mt-1.5 text-xs text-[var(--color-rust)]">{avisError}</p>}
                      <div className="mt-2 flex gap-2">
                        <button
                          type="button"
                          onClick={soumettreAvis}
                          disabled={avisSubmitting}
                          className="rounded-md bg-[var(--color-brass)] px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
                        >
                          {avisSubmitting ? "Envoi…" : "Envoyer l'avis"}
                        </button>
                        <button
                          type="button"
                          onClick={() => setAvisOuvert(false)}
                          className="rounded-md px-3 py-1.5 text-xs font-medium text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                        >
                          Annuler
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {attachmentError && (
                <p className="border-t border-[var(--color-line)] bg-[var(--color-rust-bg)] px-4 py-1.5 text-xs text-[var(--color-rust)]">
                  {attachmentError}
                </p>
              )}

              <div className="flex items-center gap-2 border-t border-[var(--color-line)] p-3">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPT_PIECE_JOINTE}
                  className="hidden"
                  onChange={handleFileInputChange}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadingFile}
                  title="Joindre une photo ou un PDF"
                  className="rounded-md border border-[var(--color-line)] p-2 text-[var(--color-ink-2)] transition-colors hover:border-[var(--color-brass)] hover:text-[var(--color-brass-deep)] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {uploadingFile ? <Loader2 size={16} className="animate-spin" /> : <Paperclip size={16} />}
                </button>
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

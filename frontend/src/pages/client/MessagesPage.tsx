import { MessageSquare, Send } from "lucide-react";

export default function MessagesPage() {
  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Messagerie</h1>
      <div className="mt-8 flex h-[520px] overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)]">
        <div className="w-72 border-r border-[var(--color-line)] p-3">
          <div className="rounded-md bg-[var(--color-paper-2)] p-3">
            <div className="text-sm font-medium text-[var(--color-ink)]">Karim El Amrani</div>
            <div className="truncate text-xs text-[var(--color-ink-3)]">
              D'accord, je vous confirme la visite jeudi.
            </div>
          </div>
        </div>
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-[var(--color-ink-3)]">
          <MessageSquare size={28} />
          <p className="max-w-xs text-center text-sm">
            Le chat temps réel (étape 8 — WebSocket / Socket.IO) sera branché ici une fois le
            back-end disponible.
          </p>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-2 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-2">
        <input
          disabled
          placeholder="Écrire un message…"
          className="flex-1 rounded-md px-3 py-2 text-sm text-[var(--color-ink-3)] outline-none"
        />
        <button disabled className="rounded-md bg-[var(--color-paper-2)] p-2 text-[var(--color-ink-3)]">
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}

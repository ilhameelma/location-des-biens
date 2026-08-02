// Étape 9 — Notifications
// Cloche de notification temps réel : badge de compteur, menu déroulant
// avec l'historique, clic pour marquer comme lu, "tout marquer comme lu".
import { useEffect, useRef, useState } from "react";
import { Bell, CalendarClock, Wallet, MessageSquare, CheckCheck, AlertTriangle } from "lucide-react";
import { useNotifications } from "../../lib/useNotifications";
import type { Notification } from "../../types";

const ICONS: Record<string, typeof Bell> = {
  reservation: CalendarClock,
  paiement: Wallet,
  message: MessageSquare,
  avertissement: AlertTriangle,
};

// Types "sensibles" affichés avec un badge d'avertissement (fond/texte rouille)
// plutôt que le style brass neutre — ex. réclamation reçue par un propriétaire.
const WARNING_TYPES = new Set(["avertissement"]);

function formatRelatif(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime();
  const min = Math.round(diffMs / 60000);
  if (min < 1) return "à l'instant";
  if (min < 60) return `il y a ${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `il y a ${h} h`;
  const j = Math.round(h / 24);
  return `il y a ${j} j`;
}

function NotificationItem({ notif, onClick }: { notif: Notification; onClick: () => void }) {
  const Icon = ICONS[notif.type_notification] ?? Bell;
  const isWarning = WARNING_TYPES.has(notif.type_notification);
  return (
    <button
      onClick={onClick}
      className={`flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-[var(--color-paper-2)] ${
        notif.lu ? "" : isWarning ? "bg-[var(--color-rust)]/8" : "bg-[var(--color-brass)]/5"
      }`}
    >
      <span
        className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
          isWarning
            ? "bg-[var(--color-rust)]/15 text-[var(--color-rust)]"
            : notif.lu
              ? "bg-[var(--color-paper-2)] text-[var(--color-ink-3)]"
              : "bg-[var(--color-brass)]/15 text-[var(--color-brass-deep)]"
        }`}
      >
        <Icon size={14} />
      </span>
      <span className="min-w-0 flex-1">
        <span
          className={`block text-sm ${
            isWarning
              ? "font-medium text-[var(--color-rust)]"
              : notif.lu
                ? "text-[var(--color-ink-2)]"
                : "text-[var(--color-ink)] font-medium"
          }`}
        >
          {notif.contenu}
        </span>
        <span className="mt-0.5 block font-mono text-[10px] text-[var(--color-ink-3)]">
          {formatRelatif(notif.date_creation)}
        </span>
      </span>
      {!notif.lu && (
        <span
          className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${
            isWarning ? "bg-[var(--color-rust)]" : "bg-[var(--color-brass)]"
          }`}
        />
      )}
    </button>
  );
}

export default function NotificationBell() {
  const { notifications, unreadCount, loading, markRead, markAllRead } = useNotifications();
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="relative text-[var(--color-ink-2)] hover:text-[var(--color-ink)]"
      >
        <Bell size={19} />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--color-rust)] px-1 text-[9px] font-semibold text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-20 mt-2 w-80 overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] shadow-lg">
          <div className="flex items-center justify-between border-b border-[var(--color-line)] px-4 py-2.5">
            <span className="text-sm font-medium text-[var(--color-ink)]">Notifications</span>
            {unreadCount > 0 && (
              <button
                onClick={() => markAllRead()}
                className="flex items-center gap-1 text-xs text-[var(--color-brass-deep)] hover:underline"
              >
                <CheckCheck size={13} />
                Tout marquer lu
              </button>
            )}
          </div>
          <div className="max-h-96 divide-y divide-[var(--color-line)] overflow-y-auto">
            {loading ? (
              <p className="px-4 py-6 text-center text-sm text-[var(--color-ink-3)]">Chargement…</p>
            ) : notifications.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-[var(--color-ink-3)]">
                Aucune notification pour le moment.
              </p>
            ) : (
              notifications.map((n) => (
                <NotificationItem key={n.id} notif={n} onClick={() => !n.lu && markRead(n.id)} />
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { History, X, Trash2 } from "lucide-react";
import { useSearchHistory } from "../../lib/useSearchHistory";
import type { CriteresRecherche } from "../../types";

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

export default function SearchHistoryPanel({
  onApply,
}: {
  onApply: (criteres: CriteresRecherche) => void;
}) {
  const { historique, loading, supprimer, viderTout } = useSearchHistory();
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
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`flex items-center gap-1.5 rounded-md border px-3 py-2 text-xs font-medium transition-colors ${
          open
            ? "border-[var(--color-brass)] text-[var(--color-brass-deep)]"
            : "border-[var(--color-line)] text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
        }`}
      >
        <History size={13} />
        Historique
        {historique.length > 0 && (
          <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--color-brass)]/15 px-1 font-mono text-[10px] text-[var(--color-brass-deep)]">
            {historique.length}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute left-0 top-full z-20 mt-2 w-[min(20rem,calc(100vw-2rem))] overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] shadow-lg">
          <div className="flex items-center justify-between border-b border-[var(--color-line)] px-4 py-2.5">
            <span className="text-sm font-medium text-[var(--color-ink)]">Recherches récentes</span>
            {historique.length > 0 && (
              <button
                type="button"
                onClick={() => viderTout()}
                className="flex items-center gap-1 text-xs text-[var(--color-ink-3)] hover:text-[var(--color-rust)]"
              >
                <Trash2 size={12} />
                Tout effacer
              </button>
            )}
          </div>
          <div className="max-h-96 divide-y divide-[var(--color-line)] overflow-y-auto">
            {loading ? (
              <p className="px-4 py-6 text-center text-sm text-[var(--color-ink-3)]">Chargement…</p>
            ) : historique.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-[var(--color-ink-3)]">
                Vos recherches récentes apparaîtront ici.
              </p>
            ) : (
              historique.map((r) => (
                <div
                  key={r.id}
                  className="group flex items-center gap-2 px-4 py-2.5 hover:bg-[var(--color-paper-2)]"
                >
                  <button
                    type="button"
                    onClick={() => {
                      onApply(r.criteres);
                      setOpen(false);
                    }}
                    className="min-w-0 flex-1 text-left"
                  >
                    <span className="block truncate text-sm text-[var(--color-ink)]">{r.label}</span>
                    <span className="mt-0.5 block font-mono text-[10px] text-[var(--color-ink-3)]">
                      {formatRelatif(r.date_recherche)}
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => supprimer(r.id)}
                    className="shrink-0 text-[var(--color-ink-3)] opacity-0 hover:text-[var(--color-rust)] group-hover:opacity-100"
                    title="Supprimer cette recherche"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

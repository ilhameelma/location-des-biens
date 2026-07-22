import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { Reclamation, StatutReclamation } from "../../types";
import StatusBadge from "../../components/ui/StatusBadge";

const NEXT_STATUT: Record<StatutReclamation, StatutReclamation | null> = {
  ouverte: "en_cours",
  en_cours: "resolue",
  resolue: null,
  rejetee: null,
};

const NEXT_LABEL: Record<string, string> = {
  en_cours: "Prendre en charge",
  resolue: "Marquer résolue",
};

export default function ReclamationsPage() {
  const [reclamations, setReclamations] = useState<Reclamation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchAll = () => {
    setLoading(true);
    api
      .get<Reclamation[]>("/reclamations")
      .then(setReclamations)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchAll, []);

  const advance = async (r: Reclamation) => {
    const next = NEXT_STATUT[r.statut];
    if (!next) return;
    setUpdating(r.id);
    try {
      await api.patch(`/reclamations/${r.id}/statut`, { statut: next });
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de mettre à jour");
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Réclamations</h1>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && reclamations.length === 0 && !error && (
        <p className="mt-6 text-sm text-[var(--color-ink-3)]">Aucune réclamation.</p>
      )}

      <div className="mt-8 space-y-3">
        {reclamations.map((r) => {
          const next = NEXT_STATUT[r.statut];
          return (
            <div key={r.id} className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4">
              <div className="flex items-center justify-between">
                <span className="font-medium text-[var(--color-ink)]">{r.type_reclamation}</span>
                <StatusBadge status={r.statut} />
              </div>
              <p className="mt-1 text-sm text-[var(--color-ink-2)]">{r.description}</p>
              <div className="mt-2 flex items-center justify-between">
                <p className="font-mono text-xs text-[var(--color-ink-3)]">
                  Signalée le {new Date(r.date_creation).toLocaleDateString("fr-MA")}
                </p>
                {next && (
                  <button
                    disabled={updating === r.id}
                    onClick={() => advance(r)}
                    className="rounded-md bg-[var(--color-brass)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
                  >
                    {NEXT_LABEL[next]}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

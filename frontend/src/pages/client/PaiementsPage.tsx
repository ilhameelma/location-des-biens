import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { Paiement } from "../../types";
import StatusBadge from "../../components/ui/StatusBadge";

const METHODE_LABELS: Record<string, string> = {
  carte_bancaire: "Carte bancaire",
  virement: "Virement",
  especes: "Espèces",
};

export default function PaiementsPage() {
  const [paiements, setPaiements] = useState<Paiement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Paiement[]>("/paiements/me")
      .then(setPaiements)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Mes paiements</h1>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && paiements.length === 0 && !error && (
        <p className="mt-6 text-sm text-[var(--color-ink-3)]">Aucun paiement pour le moment.</p>
      )}

      <div className="mt-8 space-y-3">
        {paiements.map((p) => (
          <div
            key={p.id}
            className="flex items-center justify-between rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4"
          >
            <div>
              <div className="font-mono text-base text-[var(--color-ink)]">
                {p.montant.toLocaleString("fr-MA")} MAD
              </div>
              <div className="text-xs text-[var(--color-ink-3)]">
                {METHODE_LABELS[p.methode] ?? p.methode} · {new Date(p.date_paiement).toLocaleDateString("fr-MA")}
              </div>
            </div>
            <StatusBadge status={p.statut} />
          </div>
        ))}
      </div>
    </div>
  );
}

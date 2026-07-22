import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { Paiement } from "../../types";
import StatusBadge from "../../components/ui/StatusBadge";

export default function OwnerPaiementsPage() {
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
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Paiements reçus</h1>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && paiements.length === 0 && !error && (
        <p className="mt-6 text-sm text-[var(--color-ink-3)]">Aucun paiement reçu pour le moment.</p>
      )}

      <div className="mt-8 overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)]">
        {paiements.length > 0 && (
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--color-paper-2)] font-mono text-xs uppercase tracking-wide text-[var(--color-ink-2)]">
              <tr>
                <th className="px-4 py-3">Montant</th>
                <th className="px-4 py-3">Méthode</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Statut</th>
              </tr>
            </thead>
            <tbody>
              {paiements.map((p) => (
                <tr key={p.id} className="border-t border-[var(--color-line)]">
                  <td className="px-4 py-3 font-mono text-[var(--color-ink)]">
                    {p.montant.toLocaleString("fr-MA")} MAD
                  </td>
                  <td className="px-4 py-3 text-[var(--color-ink-2)]">{p.methode}</td>
                  <td className="px-4 py-3 text-[var(--color-ink-2)]">
                    {new Date(p.date_paiement).toLocaleDateString("fr-MA")}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={p.statut} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

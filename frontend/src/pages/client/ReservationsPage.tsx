import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { Bien, Reservation } from "../../types";
import StatusBadge from "../../components/ui/StatusBadge";

export default function ReservationsPage() {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [biens, setBiens] = useState<Record<string, Bien>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Reservation[]>("/reservations/me")
      .then(async (res) => {
        setReservations(res);
        const uniqueBienIds = [...new Set(res.map((r) => r.bien_id))];
        const biensList = await Promise.all(
          uniqueBienIds.map((id) => api.get<Bien>(`/biens/${id}`).catch(() => null))
        );
        const map: Record<string, Bien> = {};
        biensList.forEach((b) => {
          if (b) map[b.id] = b;
        });
        setBiens(map);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Mes réservations</h1>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}

      {!loading && reservations.length === 0 && !error && (
        <p className="mt-6 text-sm text-[var(--color-ink-3)]">
          Aucune réservation pour le moment. Cherche un bien dans « Rechercher » pour en faire une.
        </p>
      )}

      {reservations.length > 0 && (
        <div className="mt-8 overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)]">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--color-paper-2)] font-mono text-xs uppercase tracking-wide text-[var(--color-ink-2)]">
              <tr>
                <th className="px-4 py-3">Bien</th>
                <th className="px-4 py-3">Ville</th>
                <th className="px-4 py-3">Date de début</th>
                <th className="px-4 py-3">Statut</th>
              </tr>
            </thead>
            <tbody>
              {reservations.map((r) => {
                const bien = biens[r.bien_id];
                return (
                  <tr key={r.id} className="border-t border-[var(--color-line)]">
                    <td className="px-4 py-3 font-medium text-[var(--color-ink)]">
                      {bien?.titre ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-[var(--color-ink-2)]">{bien?.ville ?? "—"}</td>
                    <td className="px-4 py-3 font-mono text-[var(--color-ink-2)]">{r.date_debut}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={r.statut} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

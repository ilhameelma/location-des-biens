import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import { api } from "../../lib/api";
import type { Bien, Reservation } from "../../types";
import StatusBadge from "../../components/ui/StatusBadge";

export default function DemandesPage() {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [biens, setBiens] = useState<Record<string, Bien>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchAll = () => {
    setLoading(true);
    api
      .get<Reservation[]>("/reservations/recues")
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
  };

  useEffect(fetchAll, []);

  const updateStatut = async (id: string, statut: "confirmee" | "refusee") => {
    setUpdating(id);
    try {
      await api.patch(`/reservations/${id}/statut`, { statut });
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de mettre à jour cette demande");
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">
        Demandes de réservation
      </h1>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && reservations.length === 0 && !error && (
        <p className="mt-6 text-sm text-[var(--color-ink-3)]">Aucune demande pour le moment.</p>
      )}

      <div className="mt-8 space-y-3">
        {reservations.map((r) => {
          const bien = biens[r.bien_id];
          return (
            <div
              key={r.id}
              className="flex items-center justify-between rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4"
            >
              <div>
                <div className="font-medium text-[var(--color-ink)]">{bien?.titre ?? "—"}</div>
                <div className="text-xs text-[var(--color-ink-3)]">À partir du {r.date_debut}</div>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={r.statut} />
                {r.statut === "en_attente" && (
                  <div className="flex gap-2">
                    <button
                      disabled={updating === r.id}
                      onClick={() => updateStatut(r.id, "confirmee")}
                      className="rounded-md bg-[var(--color-sage-bg)] p-2 text-[var(--color-sage)] hover:opacity-80 disabled:opacity-40"
                    >
                      <Check size={16} />
                    </button>
                    <button
                      disabled={updating === r.id}
                      onClick={() => updateStatut(r.id, "refusee")}
                      className="rounded-md bg-[var(--color-rust-bg)] p-2 text-[var(--color-rust)] hover:opacity-80 disabled:opacity-40"
                    >
                      <X size={16} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

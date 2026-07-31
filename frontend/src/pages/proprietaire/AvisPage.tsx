import { useEffect, useState } from "react";
import { MessageSquareText, Star } from "lucide-react";
import { api } from "../../lib/api";
import type { Avis } from "../../types";
import StarRating from "../../components/ui/StarRating";
import StatCard from "../../components/ui/StatCard";

export default function OwnerAvisPage() {
  const [avis, setAvis] = useState<Avis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Avis[]>("/avis/proprietaire/me")
      .then(setAvis)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  }, []);

  const noteMoyenne =
    avis.length > 0 ? (avis.reduce((sum, a) => sum + a.note, 0) / avis.length).toFixed(1) : "—";

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Avis de mes clients</h1>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}

      {!loading && !error && (
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-2">
          <StatCard label="Note moyenne" value={noteMoyenne} icon={Star} />
          <StatCard label="Nombre d'avis" value={String(avis.length)} icon={MessageSquareText} />
        </div>
      )}

      {!loading && avis.length === 0 && !error && (
        <p className="mt-8 flex items-center gap-2 text-sm text-[var(--color-ink-3)]">
          <MessageSquareText size={16} />
          Aucun avis pour le moment. Ils apparaîtront ici dès qu'un client en laissera un après un
          contrat terminé.
        </p>
      )}

      <div className="mt-8 space-y-3">
        {avis.map((a) => (
          <div key={a.id} className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[var(--color-ink)]">
                  {a.client_prenom ?? "Client"} {a.client_nom ?? ""}
                </p>
                <p className="text-xs text-[var(--color-ink-3)]">
                  {a.bien_titre ?? `Bien réf. ${a.bien_id.slice(0, 8)}`}
                </p>
              </div>
              <StarRating value={a.note} />
            </div>
            {a.commentaire && <p className="mt-2 text-sm text-[var(--color-ink-2)]">{a.commentaire}</p>}
            <p className="mt-2 font-mono text-xs text-[var(--color-ink-3)]">
              {new Date(a.date_creation).toLocaleDateString("fr-MA")}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

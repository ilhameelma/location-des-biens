import { useEffect, useState } from "react";
import { Star } from "lucide-react";
import { api } from "../../lib/api";
import type { Avis } from "../../types";

export default function AvisPage() {
  const [avis, setAvis] = useState<Avis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Avis[]>("/avis/me")
      .then(setAvis)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Mes avis</h1>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && avis.length === 0 && !error && (
        <p className="mt-6 text-sm text-[var(--color-ink-3)]">
          Tu n'as encore laissé aucun avis. Tu pourras en laisser un depuis un contrat terminé.
        </p>
      )}

      <div className="mt-8 space-y-3">
        {avis.map((a) => (
          <div key={a.id} className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs text-[var(--color-ink-3)]">
                Bien réf. {a.bien_id.slice(0, 8)}
              </span>
              <div className="flex items-center gap-0.5">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star
                    key={i}
                    size={14}
                    className={
                      i < a.note
                        ? "fill-[var(--color-brass)] text-[var(--color-brass)]"
                        : "text-[var(--color-line)]"
                    }
                  />
                ))}
              </div>
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

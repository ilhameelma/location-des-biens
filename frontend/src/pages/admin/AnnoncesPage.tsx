import { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";
import PropertyCard from "../../components/ui/PropertyCard";
import FraudCheckResult from "../../components/ia/FraudCheckResult";
import { api } from "../../lib/api";
import type { Bien, FraudeResponse } from "../../types";

export default function AnnoncesPage() {
  const [biens, setBiens] = useState<Bien[]>([]);
  const [loading, setLoading] = useState(true);

  const [fraudChecks, setFraudChecks] = useState<Record<string, FraudeResponse>>({});
  const [fraudLoadingId, setFraudLoadingId] = useState<string | null>(null);
  const [fraudError, setFraudError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Bien[]>("/biens")
      .then(setBiens)
      .finally(() => setLoading(false));
  }, []);

  const handleCheckFraud = async (bien: Bien) => {
    setFraudLoadingId(bien.id);
    setFraudError(null);
    try {
      const res = await api.get<FraudeResponse>(`/ia/fraude/${bien.id}`);
      setFraudChecks((prev) => ({ ...prev, [bien.id]: res }));
    } catch (err) {
      setFraudError(
        err instanceof Error ? err.message : "Vérification fraude temporairement indisponible"
      );
    } finally {
      setFraudLoadingId(null);
    }
  };

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">
        Modération des annonces
      </h1>
      <p className="mt-4 rounded-md bg-[var(--color-paper-2)] px-4 py-2 text-xs text-[var(--color-ink-2)]">
        Cette vue n'affiche pour l'instant que les biens déjà « disponibles » (endpoint de
        recherche public). Un endpoint admin listant aussi les biens « en_attente » et
        « suspendu » reste à ajouter côté back-end pour une modération complète.
      </p>

      {fraudError && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {fraudError}
        </div>
      )}

      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}

      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {biens.map((b) => (
          <div key={b.id}>
            <PropertyCard bien={b} />
            <button
              type="button"
              onClick={() => handleCheckFraud(b)}
              disabled={fraudLoadingId === b.id}
              className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-md border border-[var(--color-line)] py-1.5 text-xs font-medium text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)] disabled:opacity-50"
            >
              <ShieldAlert size={13} />
              {fraudLoadingId === b.id
                ? "Vérification…"
                : fraudChecks[b.id]
                  ? "Revérifier"
                  : "Vérifier cette annonce"}
            </button>
            {fraudChecks[b.id] && <FraudCheckResult result={fraudChecks[b.id]} />}
          </div>
        ))}
      </div>
    </div>
  );
}

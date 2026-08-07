import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { api } from "../../lib/api";
import type { EstimationResponse, TypeBien, TypeTransaction } from "../../types";

interface Props {
  ville: string;
  superficie: string;
  nb_pieces: string;
  type_bien: TypeBien;
  type_transaction: TypeTransaction;
  onApply: (prix: number) => void;
}

export default function EstimationWidget({
  ville,
  superficie,
  nb_pieces,
  type_bien,
  type_transaction,
  onApply,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EstimationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const estVente = type_transaction === "vente";

  const canEstimate = ville.trim().length > 0 && Number(superficie) > 0;

  const handleEstimate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.post<EstimationResponse>("/ia/estimation", {
        ville,
        superficie: Number(superficie),
        nb_pieces: nb_pieces ? Number(nb_pieces) : null,
        type_bien,
        type_transaction,
      });
      setResult(res);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Service d'estimation temporairement indisponible"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sm:col-span-2 rounded-md border border-dashed border-[var(--color-brass)] bg-[#f4e9df]/40 p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-medium text-[var(--color-brass-deep)]">
          <Sparkles size={14} />
          Suggestion de prix par IA
        </div>
        <button
          type="button"
          onClick={handleEstimate}
          disabled={!canEstimate || loading}
          className="flex items-center gap-1.5 rounded-md bg-[var(--color-brass)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-40"
        >
          {loading ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
          {loading ? "Calcul…" : estVente ? "Estimer le prix de vente" : "Estimer le loyer"}
        </button>
      </div>

      {!canEstimate && (
        <p className="mt-2 text-xs text-[var(--color-ink-3)]">
          Renseigne au moins la ville et la superficie pour obtenir une estimation.
        </p>
      )}

      {error && <p className="mt-2 text-xs text-[var(--color-rust)]">{error}</p>}

      {result && (
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-md bg-[var(--color-card)] p-3">
          <div>
            <div className="font-mono text-lg font-semibold text-[var(--color-ink)]">
              {result.prix_estime_dh.toLocaleString("fr-MA")} MAD
              {!estVente && (
                <span className="ml-1 text-xs font-normal text-[var(--color-ink-3)]">/ mois</span>
              )}
            </div>
            <div className="text-xs text-[var(--color-ink-3)]">
              Fourchette : {result.fourchette_basse_dh.toLocaleString("fr-MA")} –{" "}
              {result.fourchette_haute_dh.toLocaleString("fr-MA")} MAD
            </div>
          </div>
          <button
            type="button"
            onClick={() => onApply(result.prix_estime_dh)}
            className="rounded-md border border-[var(--color-brass)] px-3 py-1.5 text-xs font-medium text-[var(--color-brass-deep)] hover:bg-[#f4e9df]"
          >
            Utiliser ce prix
          </button>
        </div>
      )}

      <p className="mt-2 text-[10px] text-[var(--color-ink-3)]">
        Estimation indicative basée sur le marché — n'engage pas le prix final, à ajuster selon
        l'état et les équipements du bien.
      </p>
    </div>
  );
}

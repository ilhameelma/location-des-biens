import { MapPin } from "lucide-react";
import type { RecommandationItem } from "../../types";

export default function SimilarPropertiesPanel({
  items,
  sourceCatalogue,
}: {
  items: RecommandationItem[];
  sourceCatalogue: "reel" | "bootstrap_externe";
}) {
  if (items.length === 0) {
    return (
      <p className="mt-3 text-xs text-[var(--color-ink-3)]">
        Aucun bien similaire trouvé pour l'instant.
      </p>
    );
  }

  return (
    <div className="mt-3 rounded-md border border-[var(--color-line)] bg-[var(--color-paper-2)] p-3">
      {sourceCatalogue === "bootstrap_externe" && (
        <p className="mb-2 text-[10px] uppercase tracking-wide text-[var(--color-ink-3)]">
          Exemples du marché — catalogue SmartRent encore limité
        </p>
      )}
      <div className="space-y-2">
        {items.map((item, idx) => (
          <div
            key={item.id ?? idx}
            className="flex items-center justify-between gap-3 rounded-md bg-[var(--color-card)] px-3 py-2 text-sm"
          >
            <div className="min-w-0">
              <div className="truncate font-medium text-[var(--color-ink)]">
                {item.titre ?? "Bien similaire"}
              </div>
              <div className="flex items-center gap-1 text-xs text-[var(--color-ink-3)]">
                <MapPin size={11} />
                {item.quartier ? `${item.quartier}, ` : ""}
                {item.ville}
                {item.superficie_m2 ? ` · ${item.superficie_m2} m²` : ""}
              </div>
            </div>
            <div className="shrink-0 text-right">
              <div className="font-mono text-sm font-semibold text-[var(--color-ink)]">
                {item.prix_dh.toLocaleString("fr-MA")} MAD
              </div>
              <div className="text-[10px] text-[var(--color-ink-3)]">
                {Math.round(item.score_similarite * 100)}% similaire
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

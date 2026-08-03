import { useEffect, useState } from "react";
import { Hotel, Trees, GraduationCap, ShoppingBag } from "lucide-react";
import { api } from "../../lib/api";
import type { CategoriePoi, ProximiteBien } from "../../types";

const CATEGORIE_CONFIG: Record<
  CategoriePoi,
  { label: string; icon: typeof Hotel }
> = {
  hotel: { label: "Hôtels", icon: Hotel },
  jardin: { label: "Jardins & parcs", icon: Trees },
  ecole: { label: "Écoles & universités", icon: GraduationCap },
  commerce: { label: "Centres commerciaux", icon: ShoppingBag },
};

const ORDRE_CATEGORIES: CategoriePoi[] = ["hotel", "jardin", "ecole", "commerce"];

function formatDistance(km: number): string {
  return km < 1 ? `${Math.round(km * 1000)} m` : `${km.toFixed(1)} km`;
}

export default function NearbyPlaces({ bienId }: { bienId: string }) {
  const [data, setData] = useState<ProximiteBien | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .get<ProximiteBien>(`/biens/${bienId}/proximite`)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch(() => {
        if (!cancelled) setData(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [bienId]);

  if (loading) {
    return (
      <p className="mt-4 text-xs text-[var(--color-ink-3)]">
        Recherche des commodités à proximité…
      </p>
    );
  }

  if (!data || !data.disponible) {
    return (
      <p className="mt-4 rounded-md bg-[var(--color-paper-2)] px-4 py-3 text-xs text-[var(--color-ink-3)]">
        Les informations sur les alentours ne sont pas disponibles pour le moment.
      </p>
    );
  }

  const categoriesAvecResultats = ORDRE_CATEGORIES.filter(
    (cat) => (data.categories[cat]?.length ?? 0) > 0
  );

  if (categoriesAvecResultats.length === 0) {
    return (
      <p className="mt-4 rounded-md bg-[var(--color-paper-2)] px-4 py-3 text-xs text-[var(--color-ink-3)]">
        Aucune commodité connue (hôtel, jardin, école, centre commercial) recensée à proximité.
      </p>
    );
  }

  return (
    <div className="mt-4">
      <h3 className="font-display text-base text-[var(--color-ink)]">À proximité</h3>
      <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {categoriesAvecResultats.map((cat) => {
          const { label, icon: Icon } = CATEGORIE_CONFIG[cat];
          const pois = data.categories[cat] ?? [];
          return (
            <div
              key={cat}
              className="rounded-md border border-[var(--color-line)] bg-[var(--color-card)] p-3"
            >
              <div className="flex items-center gap-1.5 text-sm font-medium text-[var(--color-ink)]">
                <Icon size={15} className="text-[var(--color-brass-deep)]" />
                {label}
              </div>
              <ul className="mt-2 space-y-1.5">
                {pois.map((poi, i) => (
                  <li
                    key={`${poi.nom}-${i}`}
                    className="flex items-center justify-between gap-2 text-xs text-[var(--color-ink-2)]"
                  >
                    <span className="truncate">{poi.nom}</span>
                    <span className="shrink-0 font-mono text-[var(--color-ink-3)]">
                      {formatDistance(poi.distance_km)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
      <p className="mt-2 text-[10px] text-[var(--color-ink-3)]">
        Données © contributeurs OpenStreetMap.
      </p>
    </div>
  );
}

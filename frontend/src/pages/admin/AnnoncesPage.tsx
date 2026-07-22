import { useEffect, useState } from "react";
import PropertyCard from "../../components/ui/PropertyCard";
import { api } from "../../lib/api";
import type { Bien } from "../../types";

export default function AnnoncesPage() {
  const [biens, setBiens] = useState<Bien[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Bien[]>("/biens")
      .then(setBiens)
      .finally(() => setLoading(false));
  }, []);

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

      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}

      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {biens.map((b) => (
          <PropertyCard key={b.id} bien={b} />
        ))}
      </div>
    </div>
  );
}

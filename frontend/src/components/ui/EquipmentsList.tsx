import { useState } from "react";
import { trouverEquipement } from "../../lib/equipements";

interface EquipmentsListProps {
  codes: string[];
}

const NB_VISIBLES_INITIALEMENT = 8;

/**
 * Affiche "Ce que propose ce bien" sur la fiche détaillée (BienDetailPage),
 * dans le même esprit que la section équipements d'Airbnb : grille sur deux
 * colonnes, icône + libellé, avec un bouton "Afficher tous les N équipements"
 * si la liste est longue.
 */
export default function EquipmentsList({ codes }: EquipmentsListProps) {
  const [tousAffiches, setTousAffiches] = useState(false);

  if (!codes || codes.length === 0) return null;

  const equipements = codes.map((code) => ({ code, ...trouverEquipement(code) })).filter((e) => e.label);
  const visibles = tousAffiches ? equipements : equipements.slice(0, NB_VISIBLES_INITIALEMENT);

  return (
    <div className="mt-8">
      <h2 className="font-display text-lg text-[var(--color-ink)]">Ce que propose ce bien</h2>
      <div className="mt-3 grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
        {visibles.map(({ code, label, icon: Icon }) => (
          <div key={code} className="flex items-center gap-3 text-sm text-[var(--color-ink-2)]">
            {Icon && <Icon size={20} className="shrink-0 text-[var(--color-ink-3)]" />}
            <span>{label}</span>
          </div>
        ))}
      </div>
      {equipements.length > NB_VISIBLES_INITIALEMENT && (
        <button
          type="button"
          onClick={() => setTousAffiches((v) => !v)}
          className="mt-4 rounded-md border border-[var(--color-line)] px-4 py-2 text-sm font-medium text-[var(--color-ink)] hover:bg-[var(--color-paper-2)]"
        >
          {tousAffiches ? "Afficher moins" : `Afficher les ${equipements.length} équipements`}
        </button>
      )}
    </div>
  );
}

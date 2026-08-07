import { Check } from "lucide-react";
import { equipementsDisponibles } from "../../lib/equipements";
import type { TypeBien } from "../../types";

interface EquipmentsPickerProps {
  typeBien: TypeBien;
  selected: string[];
  onChange: (codes: string[]) => void;
}

/**
 * Sélecteur "façon Airbnb" des équipements/commodités d'une annonce, utilisé
 * dans le formulaire de publication et d'édition (OwnerDashboard). Le
 * catalogue proposé s'adapte automatiquement au type de bien choisi
 * (résidentiel / bureau / magasin / garage / terrain — voir lib/equipements.ts).
 */
export default function EquipmentsPicker({ typeBien, selected, onChange }: EquipmentsPickerProps) {
  const catalogue = equipementsDisponibles(typeBien);

  const toggle = (code: string) => {
    if (selected.includes(code)) {
      onChange(selected.filter((c) => c !== code));
    } else {
      onChange([...selected, code]);
    }
  };

  return (
    <div className="sm:col-span-2">
      <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
        Équipements proposés {selected.length > 0 ? `(${selected.length} sélectionné${selected.length > 1 ? "s" : ""})` : ""}
      </label>
      <p className="mb-2 text-xs text-[var(--color-ink-3)]">
        Sélectionnez ce que propose ce bien — la liste s'adapte au type de bien choisi ci-dessus.
      </p>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {catalogue.map(({ code, label, icon: Icon }) => {
          const active = selected.includes(code);
          return (
            <button
              key={code}
              type="button"
              onClick={() => toggle(code)}
              aria-pressed={active}
              className={`flex items-center gap-2 rounded-md border px-3 py-2 text-left text-xs transition ${
                active
                  ? "border-[var(--color-brass)] bg-[var(--color-brass)]/10 text-[var(--color-brass-deep)]"
                  : "border-[var(--color-line)] text-[var(--color-ink-2)] hover:border-[var(--color-brass)]"
              }`}
            >
              <Icon size={16} className="shrink-0" />
              <span className="flex-1">{label}</span>
              {active && <Check size={14} className="shrink-0" />}
            </button>
          );
        })}
      </div>
    </div>
  );
}

import { MapPin, Ruler, CalendarPlus, ImageIcon, MessageCircle } from "lucide-react";
import type { Bien } from "../../types";
import StatusBadge from "./StatusBadge";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const TYPE_LABELS: Record<string, string> = {
  maison: "Maison",
  appartement: "Appartement",
  magasin: "Magasin",
  garage: "Garage",
  bureau: "Bureau",
  terrain: "Terrain",
  villa: "Villa",
};

export default function PropertyCard({
  bien,
  onReserve,
  onContact,
}: {
  bien: Bien;
  onReserve?: (bien: Bien) => void;
  onContact?: (bien: Bien) => void;
}) {
  // --- AFFICHAGE DES PHOTOS ---
  // Étape 7 : les photos sont désormais stockées sur MinIO et l'URL
  // enregistrée en base est déjà une URL absolue
  // (ex: http://localhost:9000/smartrent-photos/biens/...).
  // On garde la compatibilité avec d'anciennes URLs relatives
  // (/uploads/photos/...) au cas où il en resterait en base.
  const rawUrl = bien.photos && bien.photos.length > 0 ? bien.photos[0].url : null;
  const firstPhotoUrl = rawUrl
    ? rawUrl.startsWith("http://") || rawUrl.startsWith("https://")
      ? rawUrl
      : `${API_BASE_URL}${rawUrl}`
    : null;
  const photoCount = bien.photos?.length ?? 0;

  return (
    <div className="group relative overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] transition-shadow hover:shadow-md">
      {/* Badge statut */}
      <div className="absolute right-3 top-3 z-10">
        <StatusBadge status={bien.statut} />
      </div>

      {/* IMAGE DU BIEN */}
      <div className="relative h-44 w-full overflow-hidden bg-[var(--color-paper-2)]">
        {firstPhotoUrl ? (
          <img
            src={firstPhotoUrl}
            alt={bien.titre}
            className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
            onError={(e) => {
              // Si l'image ne charge pas, afficher le fallback
              (e.target as HTMLImageElement).style.display = "none";
              const parent = (e.target as HTMLImageElement).parentElement;
              if (parent) {
                parent.innerHTML = `<div class="flex h-full flex-col items-center justify-center gap-2 text-gray-400">
                  <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
                  <span class="font-mono text-xs tracking-widest uppercase">Réf. ${bien.id.slice(0, 8)}</span>
                </div>`;
              }
            }}
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-[var(--color-ink-3)]">
            <ImageIcon size={28} />
            <span className="font-mono text-xs tracking-widest uppercase">
              Réf. {bien.id.slice(0, 8)}
            </span>
          </div>
        )}
        {/* Compteur de photos */}
        {photoCount > 1 && (
          <div className="absolute bottom-2 right-2 rounded-full bg-black/60 px-2 py-0.5 text-xs text-white">
            {photoCount} photos
          </div>
        )}
      </div>

      <div className="space-y-2 p-4">
        <div className="flex items-center justify-between gap-2">
          <span className="font-mono text-[11px] uppercase tracking-wide text-[var(--color-brass-deep)]">
            {TYPE_LABELS[bien.type_bien] ?? bien.type_bien}
          </span>
        </div>
        <h3 className="font-display text-lg leading-snug text-[var(--color-ink)]">
          {bien.titre}
        </h3>
        <div className="flex items-center gap-1.5 text-sm text-[var(--color-ink-2)]">
          <MapPin size={14} />
          <span>{bien.ville}</span>
        </div>
        {bien.superficie != null && (
          <div className="flex items-center gap-1.5 text-sm text-[var(--color-ink-2)]">
            <Ruler size={14} />
            <span>{bien.superficie} m²</span>
          </div>
        )}
        <div className="flex items-baseline justify-between pt-2">
          <span className="font-mono text-base font-semibold text-[var(--color-ink)]">
            {bien.prix.toLocaleString("fr-MA")} MAD
          </span>
          <span className="text-xs text-[var(--color-ink-3)]">/ mois</span>
        </div>

        <div className="mt-2 flex gap-2">
          {onContact && (
            <button
              onClick={() => onContact(bien)}
              className="flex flex-1 items-center justify-center gap-2 rounded-md border border-[var(--color-line)] py-2 text-sm font-medium text-[var(--color-ink)] transition-colors hover:bg-[var(--color-paper-2)]"
            >
              <MessageCircle size={15} />
              Contacter
            </button>
          )}
          {onReserve && bien.statut === "disponible" && (
            <button
              onClick={() => onReserve(bien)}
              className="flex flex-1 items-center justify-center gap-2 rounded-md bg-[var(--color-brass)] py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)]"
            >
              <CalendarPlus size={15} />
              Réserver
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
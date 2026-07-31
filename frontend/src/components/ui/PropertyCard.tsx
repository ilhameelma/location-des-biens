import { Link } from "react-router-dom";
import { MapPin, Ruler, CalendarPlus, MessageCircle, Tag, Heart } from "lucide-react";
import type { Bien } from "../../types";
import StatusBadge from "./StatusBadge";
import ImageCarousel from "./ImageCarousel";

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
  isFavori,
  onToggleFavori,
}: {
  bien: Bien;
  onReserve?: (bien: Bien) => void;
  onContact?: (bien: Bien) => void;
  /** Si fourni (avec onToggleFavori), affiche le bouton "cœur" enregistrer/retirer. */
  isFavori?: boolean;
  onToggleFavori?: (bien: Bien) => void;
}) {
  const isVente = bien.type_transaction === "vente";

  return (
    <div className="group relative overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] transition-shadow hover:shadow-md">
      {/* Bouton "enregistrer" (cœur) — coin haut-gauche, opposé aux badges de statut */}
      {onToggleFavori && (
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onToggleFavori(bien);
          }}
          aria-label={isFavori ? "Retirer des annonces enregistrées" : "Enregistrer cette annonce"}
          className={`absolute left-3 top-3 z-10 flex h-8 w-8 items-center justify-center rounded-full bg-white/90 shadow-sm transition-colors hover:bg-white ${
            isFavori ? "text-[var(--color-rust)]" : "text-[var(--color-ink-2)]"
          }`}
        >
          <Heart size={16} className={isFavori ? "fill-current" : ""} />
        </button>
      )}

      {/* Badges statut + type de transaction */}
      <div className="absolute right-3 top-3 z-10 flex flex-col items-end gap-1.5">
        <StatusBadge status={bien.statut} />
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium font-mono tracking-wide uppercase ${
            isVente ? "bg-[#f4e9df] text-[var(--color-brass-deep)]" : "bg-white/90 text-[var(--color-ink-2)]"
          }`}
        >
          <Tag size={11} />
          {isVente ? "À vendre" : "À louer"}
        </span>
      </div>

      {/* Zone cliquable menant à la fiche détaillée (photos + infos, hors boutons d'action) */}
      <Link to={`/biens/${bien.id}`}>
        <ImageCarousel photos={bien.photos} alt={bien.titre} refLabel={bien.id.slice(0, 8)} />

        <div className="space-y-2 p-4 pb-0">
          <div className="flex items-center justify-between gap-2">
            <span className="font-mono text-[11px] uppercase tracking-wide text-[var(--color-brass-deep)]">
              {TYPE_LABELS[bien.type_bien] ?? bien.type_bien}
            </span>
          </div>
          <h3 className="font-display text-lg leading-snug text-[var(--color-ink)] transition-colors group-hover:text-[var(--color-brass-deep)]">
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
            {!isVente && <span className="text-xs text-[var(--color-ink-3)]">/ mois</span>}
          </div>
        </div>
      </Link>

      <div className="space-y-2 p-4 pt-2">
        <div className="flex gap-2">
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
              {isVente ? "Faire une offre" : "Réserver"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

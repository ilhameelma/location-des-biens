import { useState } from "react";
import { ChevronLeft, ChevronRight, ImageIcon } from "lucide-react";
import type { PhotoBien } from "../../types";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function resolvePhotoUrl(url: string): string {
  return url.startsWith("http://") || url.startsWith("https://") ? url : `${API_BASE_URL}${url}`;
}

/**
 * Carrousel d'images générique : flèches précédent/suivant + pagination par
 * points. Utilisé en version compacte dans PropertyCard (liste/recherche) et
 * en version large dans BienDetailPage (fiche détaillée d'une annonce).
 */
export default function ImageCarousel({
  photos,
  alt,
  heightClass = "h-44",
  refLabel,
  rounded = false,
  showCounter = true,
  index: controlledIndex,
  onIndexChange,
}: {
  photos: PhotoBien[];
  alt: string;
  heightClass?: string;
  refLabel?: string;
  rounded?: boolean;
  showCounter?: boolean;
  index?: number;
  onIndexChange?: (index: number) => void;
}) {
  const sorted = [...photos].sort((a, b) => a.ordre - b.ordre);
  const [internalIndex, setInternalIndex] = useState(0);
  const index = controlledIndex ?? internalIndex;
  const count = sorted.length;

  const goTo = (i: number, e?: React.MouseEvent) => {
    e?.preventDefault();
    e?.stopPropagation();
    const next = (i + count) % count;
    if (onIndexChange) onIndexChange(next);
    else setInternalIndex(next);
  };

  if (count === 0) {
    return (
      <div
        className={`flex ${heightClass} w-full flex-col items-center justify-center gap-2 bg-[var(--color-paper-2)] text-[var(--color-ink-3)] ${rounded ? "rounded-lg" : ""}`}
      >
        <ImageIcon size={28} />
        {refLabel && (
          <span className="font-mono text-xs tracking-widest uppercase">Réf. {refLabel}</span>
        )}
      </div>
    );
  }

  const current = sorted[index];

  return (
    <div
      className={`group/carousel relative ${heightClass} w-full overflow-hidden bg-[var(--color-paper-2)] ${rounded ? "rounded-lg" : ""}`}
    >
      <img
        src={resolvePhotoUrl(current.url)}
        alt={`${alt} — photo ${index + 1}/${count}`}
        className="h-full w-full object-cover transition duration-300"
        onError={(e) => {
          (e.target as HTMLImageElement).style.display = "none";
        }}
      />

      {count > 1 && (
        <>
          {/* Flèches précédent / suivant — visibles au survol sur desktop, toujours visibles sur mobile */}
          <button
            type="button"
            aria-label="Image précédente"
            onClick={(e) => goTo(index - 1, e)}
            className="absolute left-2 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white opacity-80 transition hover:bg-black/70 group-hover/carousel:opacity-100"
          >
            <ChevronLeft size={16} />
          </button>
          <button
            type="button"
            aria-label="Image suivante"
            onClick={(e) => goTo(index + 1, e)}
            className="absolute right-2 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-white opacity-80 transition hover:bg-black/70 group-hover/carousel:opacity-100"
          >
            <ChevronRight size={16} />
          </button>

          {/* Pagination par points */}
          <div className="absolute bottom-2 left-1/2 flex -translate-x-1/2 gap-1.5">
            {sorted.map((p, i) => (
              <button
                key={p.id}
                type="button"
                aria-label={`Aller à l'image ${i + 1}`}
                onClick={(e) => goTo(i, e)}
                className={`h-1.5 rounded-full transition-all ${
                  i === index ? "w-4 bg-white" : "w-1.5 bg-white/50 hover:bg-white/80"
                }`}
              />
            ))}
          </div>

          {showCounter && (
            <div className="absolute right-2 top-2 rounded-full bg-black/60 px-2 py-0.5 text-xs text-white">
              {index + 1}/{count}
            </div>
          )}
        </>
      )}
    </div>
  );
}

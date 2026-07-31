import { Star } from "lucide-react";

export default function StarRating({
  value,
  onChange,
  size = 14,
}: {
  value: number;
  onChange?: (note: number) => void;
  size?: number;
}) {
  const interactive = Boolean(onChange);

  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, i) => {
        const filled = i < value;
        return (
          <button
            key={i}
            type="button"
            disabled={!interactive}
            onClick={() => onChange?.(i + 1)}
            className={interactive ? "cursor-pointer" : "cursor-default"}
            aria-label={`${i + 1} étoile${i > 0 ? "s" : ""}`}
          >
            <Star
              size={size}
              className={filled ? "fill-[var(--color-brass)] text-[var(--color-brass)]" : "text-[var(--color-line)]"}
            />
          </button>
        );
      })}
    </div>
  );
}

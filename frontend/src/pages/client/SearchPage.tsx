import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search } from "lucide-react";
import PropertyCard from "../../components/ui/PropertyCard";
import { api } from "../../lib/api";
import type { Bien, Conversation, TypeBien } from "../../types";

const TYPES: { value: TypeBien | "tous"; label: string }[] = [
  { value: "tous", label: "Tous types" },
  { value: "appartement", label: "Appartement" },
  { value: "maison", label: "Maison" },
  { value: "bureau", label: "Bureau" },
  { value: "magasin", label: "Magasin" },
  { value: "garage", label: "Garage" },
  { value: "terrain", label: "Terrain" },
];

export default function SearchPage() {
  const navigate = useNavigate();
  const [ville, setVille] = useState("");
  const [type, setType] = useState<TypeBien | "tous">("tous");
  const [biens, setBiens] = useState<Bien[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const fetchBiens = () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (ville) params.set("ville", ville);
    if (type !== "tous") params.set("type_bien", type);
    api
      .get<Bien[]>(`/biens?${params.toString()}`)
      .then(setBiens)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(fetchBiens, [ville, type]);

  const handleReserve = async (bien: Bien) => {
    const dateDebut = window.prompt(
      `Date de début de la réservation pour "${bien.titre}" (format AAAA-MM-JJ) :`,
      new Date().toISOString().slice(0, 10)
    );
    if (!dateDebut) return;

    try {
      await api.post("/reservations", { bien_id: bien.id, date_debut: dateDebut });
      setMessage("Demande de réservation envoyée au propriétaire !");
      setTimeout(() => setMessage(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de réserver ce bien");
    }
  };

  const handleContact = async (bien: Bien) => {
    try {
      const conv = await api.post<Conversation>("/conversations", {
        proprietaire_id: bien.proprietaire_id,
        bien_id: bien.id,
      });
      navigate(`/client/messages?conv=${conv.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de démarrer la conversation");
    }
  };

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">
        Rechercher un bien
      </h1>

      {message && (
        <div className="mt-4 rounded-md bg-[var(--color-sage-bg)] px-4 py-2 text-sm text-[var(--color-sage)]">
          {message}
        </div>
      )}
      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}

      <div className="mt-6 mb-6 flex flex-wrap items-center gap-3 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-ink-3)]" />
          <input
            value={ville}
            onChange={(e) => setVille(e.target.value)}
            placeholder="Ville (ex. Casablanca)"
            className="w-full rounded-md border border-[var(--color-line)] py-2 pl-9 pr-3 text-sm outline-none focus:border-[var(--color-brass)]"
          />
        </div>
        <select
          value={type}
          onChange={(e) => setType(e.target.value as TypeBien | "tous")}
          className="rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
        >
          {TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        <span className="ml-auto font-mono text-xs text-[var(--color-ink-3)]">
          {loading ? "Recherche…" : `${biens.length} bien(s) trouvé(s)`}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {biens.map((b) => (
          <PropertyCard key={b.id} bien={b} onReserve={handleReserve} onContact={handleContact} />
        ))}
      </div>

      {!loading && biens.length === 0 && (
        <p className="mt-8 text-center text-sm text-[var(--color-ink-3)]">
          Aucun bien disponible pour ces critères pour le moment.
        </p>
      )}
    </div>
  );
}

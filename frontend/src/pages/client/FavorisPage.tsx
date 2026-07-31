import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Heart } from "lucide-react";
import PropertyCard from "../../components/ui/PropertyCard";
import { api } from "../../lib/api";
import { emitFavorisChanged } from "../../lib/favorisEvents";
import type { Bien, Conversation } from "../../types";

export default function FavorisPage() {
  const navigate = useNavigate();
  const [biens, setBiens] = useState<Bien[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const fetchFavoris = () => {
    setLoading(true);
    api
      .get<Bien[]>("/favoris/me")
      .then(setBiens)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchFavoris, []);

  const handleRemove = async (bien: Bien) => {
    // Retrait optimiste : l'annonce disparaît immédiatement de la liste,
    // sans attendre la confirmation du serveur.
    setBiens((prev) => prev.filter((b) => b.id !== bien.id));
    try {
      await api.del(`/favoris/${bien.id}`);
      emitFavorisChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de retirer cette annonce");
      fetchFavoris();
    }
  };

  const handleReserve = async (bien: Bien) => {
    const dateDebut = window.prompt(
      bien.type_transaction === "vente"
        ? `Date souhaitée pour votre offre sur "${bien.titre}" (format AAAA-MM-JJ) :`
        : `Date de début de la réservation pour "${bien.titre}" (format AAAA-MM-JJ) :`,
      new Date().toISOString().slice(0, 10)
    );
    if (!dateDebut) return;
    try {
      await api.post("/reservations", { bien_id: bien.id, date_debut: dateDebut });
      setMessage(
        bien.type_transaction === "vente"
          ? "Votre offre a été envoyée au propriétaire !"
          : "Demande de réservation envoyée au propriétaire !"
      );
      setTimeout(() => setMessage(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d'envoyer la demande");
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
        Annonces enregistrées {!loading && `(${biens.length})`}
      </h1>
      <p className="mt-1 text-sm text-[var(--color-ink-3)]">
        Les biens que vous avez mis de côté — cliquez sur le cœur pour les retirer.
      </p>

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

      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}

      {!loading && biens.length === 0 && !error && (
        <div className="mt-10 flex flex-col items-center gap-2 rounded-lg border border-dashed border-[var(--color-line)] py-14 text-center">
          <Heart size={28} className="text-[var(--color-ink-3)]" />
          <p className="text-sm text-[var(--color-ink-2)]">
            Aucune annonce enregistrée pour l'instant.
          </p>
          <p className="text-xs text-[var(--color-ink-3)]">
            Ouvrez une annonce et cliquez sur le cœur pour la retrouver ici.
          </p>
        </div>
      )}

      {!loading && biens.length > 0 && (
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {biens.map((b) => (
            <PropertyCard
              key={b.id}
              bien={b}
              onReserve={handleReserve}
              onContact={handleContact}
              isFavori
              onToggleFavori={handleRemove}
            />
          ))}
        </div>
      )}
    </div>
  );
}

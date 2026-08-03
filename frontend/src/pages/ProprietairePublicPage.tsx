import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Star, Home, CalendarDays } from "lucide-react";
import PropertyCard from "../components/ui/PropertyCard";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { Bien, Conversation, ProprietairePublic } from "../types";

function formatMembreDepuis(dateIso: string): string {
  const date = new Date(dateIso);
  return date.toLocaleDateString("fr-FR", { month: "long", year: "numeric" });
}

export default function ProprietairePublicPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [profil, setProfil] = useState<ProprietairePublic | null>(null);
  const [biens, setBiens] = useState<Bien[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);
    Promise.all([
      api.get<ProprietairePublic>(`/utilisateurs/${id}/profil-public`),
      api.get<Bien[]>(`/biens/proprietaire/${id}`),
    ])
      .then(([p, b]) => {
        setProfil(p);
        setBiens(b);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Ce propriétaire est introuvable")
      )
      .finally(() => setLoading(false));
  }, [id]);

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

  if (loading) {
    return <p className="text-sm text-[var(--color-ink-3)]">Chargement du profil…</p>;
  }

  if (error || !profil) {
    return (
      <div>
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mb-4 flex items-center gap-1.5 text-sm text-[var(--color-ink-2)] hover:text-[var(--color-brass-deep)]"
        >
          <ArrowLeft size={15} />
          Retour
        </button>
        <div className="rounded-md bg-[var(--color-rust-bg)] px-4 py-3 text-sm text-[var(--color-rust)]">
          {error ?? "Ce propriétaire est introuvable."}
        </div>
      </div>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="mb-4 flex items-center gap-1.5 text-sm text-[var(--color-ink-2)] hover:text-[var(--color-brass-deep)]"
      >
        <ArrowLeft size={15} />
        Retour
      </button>

      {message && (
        <div className="mb-4 rounded-md bg-[var(--color-sage-bg)] px-4 py-2 text-sm text-[var(--color-sage)]">
          {message}
        </div>
      )}
      {error && (
        <div className="mb-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}

      {/* En-tête profil */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-5">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-paper-2)] font-display text-xl text-[var(--color-brass-deep)]">
            {profil.prenom.charAt(0)}
            {profil.nom.charAt(0)}
          </div>
          <div>
            <h1 className="font-display text-xl text-[var(--color-ink)]">
              {profil.prenom} {profil.nom}
            </h1>
            <p className="mt-0.5 flex items-center gap-1.5 text-xs text-[var(--color-ink-3)]">
              <CalendarDays size={12} />
              Membre depuis {formatMembreDepuis(profil.date_creation)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 font-mono text-lg font-semibold text-[var(--color-ink)]">
              <Home size={15} />
              {profil.nb_biens_actifs}
            </div>
            <p className="text-xs text-[var(--color-ink-3)]">annonce(s) active(s)</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 font-mono text-lg font-semibold text-[var(--color-ink)]">
              <Star size={15} className={profil.note_moyenne ? "fill-[var(--color-brass)] text-[var(--color-brass)]" : ""} />
              {profil.note_moyenne != null ? profil.note_moyenne.toFixed(1) : "—"}
            </div>
            <p className="text-xs text-[var(--color-ink-3)]">
              {profil.nb_avis > 0 ? `${profil.nb_avis} avis` : "aucun avis"}
            </p>
          </div>
        </div>
      </div>

      {/* Annonces du propriétaire */}
      <div className="mt-8">
        <h2 className="font-display text-lg text-[var(--color-ink)]">
          Annonces de {profil.prenom} ({biens.length})
        </h2>

        {biens.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--color-ink-3)]">
            Ce propriétaire n'a aucune annonce disponible pour le moment.
          </p>
        ) : (
          <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {biens.map((b) => (
              <PropertyCard
                key={b.id}
                bien={b}
                onReserve={user?.role === "client" ? handleReserve : undefined}
                onContact={user?.role === "client" ? handleContact : undefined}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

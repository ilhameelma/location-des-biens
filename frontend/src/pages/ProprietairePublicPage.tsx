import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Star, Home, CalendarDays, MessageSquareText } from "lucide-react";
import PropertyCard from "../components/ui/PropertyCard";
import StarRating from "../components/ui/StarRating";
import ReservationPaymentModal from "../components/reservation/ReservationPaymentModal";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { labelAnnonceur } from "../lib/roles";
import type { Avis, Bien, Conversation, ProprietairePublic } from "../types";

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
  const [avis, setAvis] = useState<Avis[]>([]);
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

    // Avis publics laissés par les clients sur ce propriétaire — best-effort,
    // un échec ici n'empêche pas d'afficher le reste du profil/des annonces.
    api
      .get<Avis[]>(`/avis/proprietaire/${id}`)
      .then(setAvis)
      .catch(() => setAvis([]));
  }, [id]);

  // Bien en cours de réservation via la modale de paiement instantané
  // (carte/virement) — uniquement pour les locations, voir handleReserve.
  const [reserveBien, setReserveBien] = useState<Bien | null>(null);

  const handleReserve = async (bien: Bien) => {
    if (bien.type_transaction === "vente") {
      const dateDebut = window.prompt(
        `Date souhaitée pour votre offre sur "${bien.titre}" (format AAAA-MM-JJ) :`,
        new Date().toISOString().slice(0, 10)
      );
      if (!dateDebut) return;
      try {
        await api.post("/reservations", { bien_id: bien.id, date_debut: dateDebut });
        setMessage("Votre offre a été envoyée au propriétaire !");
        setTimeout(() => setMessage(null), 4000);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Impossible d'envoyer la demande");
      }
      return;
    }
    setReserveBien(bien);
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
              {profil.raison_sociale || `${profil.prenom} ${profil.nom}`}
            </h1>
            <p className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-[var(--color-ink-3)]">
              <span className="rounded-full bg-[var(--color-paper-2)] px-2 py-0.5 font-medium text-[var(--color-ink-2)]">
                {labelAnnonceur(profil.role)}
              </span>
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
          Annonces de {profil.raison_sociale || profil.prenom} ({biens.length})
        </h2>

        {biens.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--color-ink-3)]">
            Cet annonceur n'a aucune annonce disponible pour le moment.
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

      {/* Avis clients sur ce propriétaire */}
      <div className="mt-8">
        <h2 className="font-display text-lg text-[var(--color-ink)]">
          Avis clients ({avis.length})
        </h2>

        {avis.length === 0 ? (
          <p className="mt-4 flex items-center gap-2 text-sm text-[var(--color-ink-3)]">
            <MessageSquareText size={16} />
            Aucun avis pour le moment.
          </p>
        ) : (
          <div className="mt-4 space-y-3">
            {avis.map((a) => (
              <div
                key={a.id}
                className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-[var(--color-ink)]">
                      {a.client_prenom ?? "Client"} {a.client_nom ?? ""}
                    </p>
                    <p className="text-xs text-[var(--color-ink-3)]">
                      {a.bien_titre ?? `Bien réf. ${a.bien_id.slice(0, 8)}`}
                    </p>
                  </div>
                  <StarRating value={a.note} />
                </div>
                {a.commentaire && (
                  <p className="mt-2 text-sm text-[var(--color-ink-2)]">{a.commentaire}</p>
                )}
                <p className="mt-2 font-mono text-xs text-[var(--color-ink-3)]">
                  {new Date(a.date_creation).toLocaleDateString("fr-MA")}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      <ReservationPaymentModal
        bien={reserveBien}
        onClose={() => setReserveBien(null)}
        onSuccess={() => {
          setMessage("Réservation confirmée et payée !");
          setTimeout(() => setMessage(null), 4000);
        }}
      />
    </div>
  );
}

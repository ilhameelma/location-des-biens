import { useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import {
  ArrowLeft,
  MapPin,
  Ruler,
  Home,
  Tag,
  CalendarPlus,
  MessageCircle,
  Heart,
  Flag,
} from "lucide-react";
import ImageCarousel, { resolvePhotoUrl } from "../components/ui/ImageCarousel";
import StatusBadge from "../components/ui/StatusBadge";
import PropertiesMap from "../components/map/PropertiesMap";
import NearbyPlaces from "../components/map/NearbyPlaces";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { emitFavorisChanged } from "../lib/favorisEvents";
import type { Bien, Conversation } from "../types";

const TYPE_LABELS: Record<string, string> = {
  maison: "Maison",
  appartement: "Appartement",
  magasin: "Magasin",
  garage: "Garage",
  bureau: "Bureau",
  terrain: "Terrain",
  villa: "Villa",
};

export default function BienDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [bien, setBien] = useState<Bien | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isFavori, setIsFavori] = useState(false);
  const [favoriBusy, setFavoriBusy] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api
      .get<Bien>(`/biens/${id}`)
      .then((b) => {
        setBien(b);
        setActiveIndex(0);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Bien introuvable"))
      .finally(() => setLoading(false));
  }, [id]);

  // Enregistrement de l'annonce (favoris) — uniquement pertinent pour un client.
  useEffect(() => {
    if (!id || user?.role !== "client") return;
    api
      .get<string[]>("/favoris/me/ids")
      .then((ids) => setIsFavori(ids.includes(id)))
      .catch(() => {
        /* silencieux : l'état "enregistré" reste simplement à false */
      });
  }, [id, user]);

  const handleToggleFavori = async () => {
    if (!bien) return;
    setFavoriBusy(true);
    try {
      if (isFavori) {
        await api.del(`/favoris/${bien.id}`);
        setIsFavori(false);
      } else {
        await api.post("/favoris", { bien_id: bien.id });
        setIsFavori(true);
      }
      emitFavorisChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de mettre à jour les favoris");
    } finally {
      setFavoriBusy(false);
    }
  };

  const handleReserve = async () => {
    if (!bien) return;
    const dateDebut = window.prompt(
      `Date de début pour "${bien.titre}" (format AAAA-MM-JJ) :`,
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

  const handleContact = async () => {
    if (!bien) return;
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
    return <p className="text-sm text-[var(--color-ink-3)]">Chargement de l'annonce…</p>;
  }

  if (error || !bien) {
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
          {error ?? "Cette annonce n'existe pas ou n'est plus disponible."}
        </div>
      </div>
    );
  }

  const isVente = bien.type_transaction === "vente";
  const sortedPhotos = [...bien.photos].sort((a, b) => a.ordre - b.ordre);

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

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {/* Galerie photo — grande image + vignettes cliquables */}
          <div className="overflow-hidden rounded-lg border border-[var(--color-line)]">
            <ImageCarousel
              photos={sortedPhotos}
              alt={bien.titre}
              heightClass="h-[420px]"
              refLabel={bien.id.slice(0, 8)}
              showCounter={false}
              index={activeIndex}
              onIndexChange={setActiveIndex}
            />
          </div>
          {sortedPhotos.length > 1 && (
            <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
              {sortedPhotos.map((p, i) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setActiveIndex(i)}
                  className={`h-16 w-24 shrink-0 overflow-hidden rounded-md border-2 transition ${
                    i === activeIndex ? "border-[var(--color-brass)]" : "border-transparent opacity-70 hover:opacity-100"
                  }`}
                >
                  <img src={resolvePhotoUrl(p.url)} alt="" className="h-full w-full object-cover" />
                </button>
              ))}
            </div>
          )}

          {/* Description */}
          <div className="mt-8">
            <h2 className="font-display text-lg text-[var(--color-ink)]">Description</h2>
            <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-[var(--color-ink-2)]">
              {bien.description || "Aucune description fournie par le propriétaire."}
            </p>
          </div>

          {/* Localisation sur la carte */}
          <div className="mt-8">
            <h2 className="font-display text-lg text-[var(--color-ink)]">Localisation</h2>
            <p className="mt-1 mb-3 flex items-center gap-1.5 text-sm text-[var(--color-ink-2)]">
              <MapPin size={14} />
              {bien.adresse}, {bien.ville}
            </p>
            {bien.latitude != null && bien.longitude != null ? (
              <>
                <PropertiesMap biens={[bien]} />
                <NearbyPlaces bienId={bien.id} />
              </>
            ) : (
              <p className="rounded-md bg-[var(--color-paper-2)] px-4 py-3 text-xs text-[var(--color-ink-3)]">
                Ce bien n'a pas encore été géolocalisé par le propriétaire.
              </p>
            )}
          </div>
        </div>

        {/* Colonne latérale : infos clés + actions */}
        <div className="lg:col-span-1">
          <div className="sticky top-6 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge status={bien.statut} />
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium font-mono tracking-wide uppercase ${
                    isVente ? "bg-[#f4e9df] text-[var(--color-brass-deep)]" : "bg-[var(--color-paper-2)] text-[var(--color-ink-2)]"
                  }`}
                >
                  <Tag size={11} />
                  {isVente ? "À vendre" : "À louer"}
                </span>
              </div>
              {user?.role === "client" && (
                <button
                  type="button"
                  onClick={handleToggleFavori}
                  disabled={favoriBusy}
                  aria-label={isFavori ? "Retirer des annonces enregistrées" : "Enregistrer cette annonce"}
                  className={`flex h-9 w-9 items-center justify-center rounded-full border transition-colors disabled:opacity-60 ${
                    isFavori
                      ? "border-[var(--color-rust)] text-[var(--color-rust)]"
                      : "border-[var(--color-line)] text-[var(--color-ink-2)] hover:border-[var(--color-rust)] hover:text-[var(--color-rust)]"
                  }`}
                >
                  <Heart size={16} className={isFavori ? "fill-current" : ""} />
                </button>
              )}
            </div>

            <h1 className="mt-3 font-display text-2xl leading-snug text-[var(--color-ink)]">
              {bien.titre}
            </h1>

            <div className="mt-1 flex items-center gap-1.5 text-sm text-[var(--color-ink-2)]">
              <Home size={14} />
              {TYPE_LABELS[bien.type_bien] ?? bien.type_bien}
            </div>
            <div className="mt-1 flex items-center gap-1.5 text-sm text-[var(--color-ink-2)]">
              <MapPin size={14} />
              {bien.ville}
            </div>
            {bien.superficie != null && (
              <div className="mt-1 flex items-center gap-1.5 text-sm text-[var(--color-ink-2)]">
                <Ruler size={14} />
                {bien.superficie} m²{bien.nb_pieces != null ? ` · ${bien.nb_pieces} pièce(s)` : ""}
              </div>
            )}

            <div className="mt-4 border-t border-[var(--color-line)] pt-4">
              <span className="font-mono text-2xl font-semibold text-[var(--color-ink)]">
                {bien.prix.toLocaleString("fr-MA")} MAD
              </span>
              {!isVente && <span className="ml-1 text-sm text-[var(--color-ink-3)]">/ mois</span>}
            </div>

            {/* Publié par — lien vers la fiche profil publique du propriétaire
                (ses autres annonces + note moyenne), masqué si le visiteur
                est le propriétaire lui-même (il a déjà "Gérer cette annonce"). */}
            {!(user?.role === "proprietaire" && bien.proprietaire_id === user.id) && (
              <Link
                to={`/proprietaires/${bien.proprietaire_id}`}
                className="mt-4 flex items-center justify-between gap-2 rounded-md border border-[var(--color-line)] px-3 py-2.5 text-sm transition-colors hover:border-[var(--color-brass)]"
              >
                <span className="text-[var(--color-ink-3)]">
                  Publié par{" "}
                  <span className="font-medium text-[var(--color-ink)]">
                    {bien.proprietaire_prenom ?? "ce"} {bien.proprietaire_nom ?? "propriétaire"}
                  </span>
                </span>
                <span className="whitespace-nowrap text-xs font-medium text-[var(--color-brass-deep)]">
                  Voir ses annonces
                </span>
              </Link>
            )}

            {user?.role === "client" && (
              <div className="mt-5 flex flex-col gap-2">
                <button
                  type="button"
                  onClick={handleContact}
                  className="flex items-center justify-center gap-2 rounded-md border border-[var(--color-line)] py-2.5 text-sm font-medium text-[var(--color-ink)] transition-colors hover:bg-[var(--color-paper-2)]"
                >
                  <MessageCircle size={15} />
                  Contacter le propriétaire
                </button>
                {bien.statut === "disponible" && (
                  <button
                    type="button"
                    onClick={handleReserve}
                    className="flex items-center justify-center gap-2 rounded-md bg-[var(--color-brass)] py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)]"
                  >
                    <CalendarPlus size={15} />
                    {isVente ? "Faire une offre" : "Réserver"}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/client/reclamations?bien_id=${bien.id}&titre=${encodeURIComponent(bien.titre)}`
                    )
                  }
                  className="flex items-center justify-center gap-2 py-1.5 text-xs font-medium text-[var(--color-ink-3)] transition-colors hover:text-[var(--color-rust)]"
                >
                  <Flag size={13} />
                  Signaler cette annonce
                </button>
              </div>
            )}

            {user?.role === "proprietaire" && bien.proprietaire_id === user.id && (
              <Link
                to="/proprietaire"
                className="mt-5 flex items-center justify-center gap-2 rounded-md border border-dashed border-[var(--color-line)] py-2.5 text-sm font-medium text-[var(--color-ink-2)] hover:border-[var(--color-brass)] hover:text-[var(--color-brass-deep)]"
              >
                Gérer cette annonce
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Sparkles, LayoutGrid, Map as MapIcon, SlidersHorizontal } from "lucide-react";
import PropertyCard from "../../components/ui/PropertyCard";
import SimilarPropertiesPanel from "../../components/ia/SimilarPropertiesPanel";
import PropertiesMap from "../../components/map/PropertiesMap";
import SearchHistoryPanel from "../../components/search/SearchHistoryPanel";
import ReservationPaymentModal from "../../components/reservation/ReservationPaymentModal";
import { useSearchHistory } from "../../lib/useSearchHistory";
import { api } from "../../lib/api";
import type {
  Bien,
  Conversation,
  CriteresRecherche,
  RecommandationResponse,
  TypeBien,
  TypeTransaction,
} from "../../types";

const TYPES: { value: TypeBien | "tous"; label: string }[] = [
  { value: "tous", label: "Tous types" },
  { value: "appartement", label: "Appartement" },
  { value: "maison", label: "Maison" },
  { value: "villa", label: "Villa" },
  { value: "bureau", label: "Bureau" },
  { value: "magasin", label: "Magasin" },
  { value: "garage", label: "Garage" },
  { value: "terrain", label: "Terrain" },
];

export default function SearchPage() {
  const navigate = useNavigate();
  const [transactionType, setTransactionType] = useState<TypeTransaction>("location");
  const [ville, setVille] = useState("");
  const [type, setType] = useState<TypeBien | "tous">("tous");
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [prixMin, setPrixMin] = useState("");
  const [prixMax, setPrixMax] = useState("");
  const [superficieMin, setSuperficieMin] = useState("");
  const [tri, setTri] = useState<"pertinence" | "prix_asc" | "prix_desc" | "recent">(
    "pertinence"
  );
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [biens, setBiens] = useState<Bien[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [similarFor, setSimilarFor] = useState<string | null>(null);
  const [similarResults, setSimilarResults] = useState<RecommandationResponse | null>(null);
  const [similarLoading, setSimilarLoading] = useState(false);

  const [view, setView] = useState<"liste" | "carte">("liste");

  // Historique de recherche : le hook gère le chargement/l'enregistrement/la
  // suppression ; on l'utilise ici uniquement pour `enregistrer` (le panneau
  // déroulant, lui, recharge sa propre copie de la liste).
  const { enregistrer } = useSearchHistory();
  // Évite de ré-enregistrer immédiatement une entrée qu'on vient d'appliquer
  // depuis l'historique (la recherche resterait identique à celle cliquée).
  const skipProchainEnregistrement = useRef(false);

  // Étape 18 — Recherche avancée : le texte libre part vers Elasticsearch
  // (titre/ville/adresse/description) ; on le débounce pour ne pas envoyer
  // une requête à chaque frappe.
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 350);
    return () => clearTimeout(t);
  }, [q]);

  const fetchBiens = () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    params.set("type_transaction", transactionType);
    if (ville) params.set("ville", ville);
    if (type !== "tous") params.set("type_bien", type);
    if (debouncedQ) params.set("q", debouncedQ);
    if (prixMin) params.set("prix_min", prixMin);
    if (prixMax) params.set("prix_max", prixMax);
    if (superficieMin) params.set("superficie_min", superficieMin);
    if (tri !== "pertinence") params.set("tri", tri);
    api
      .get<Bien[]>(`/biens?${params.toString()}`)
      .then(setBiens)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(fetchBiens, [transactionType, ville, type, debouncedQ, prixMin, prixMax, superficieMin, tri]);

  // Construit un libellé lisible ("Location · Casablanca · Appartement ·
  // 3 000–6 000 MAD") à partir des filtres actifs, affiché dans le panneau
  // d'historique.
  const buildLabel = (): string => {
    const parts: string[] = [transactionType === "vente" ? "Achat" : "Location"];
    if (ville) parts.push(ville);
    if (type !== "tous") {
      const found = TYPES.find((t) => t.value === type);
      if (found) parts.push(found.label);
    }
    if (debouncedQ) parts.push(`« ${debouncedQ} »`);
    if (prixMin || prixMax) parts.push(`${prixMin || "0"}–${prixMax || "∞"} MAD`);
    if (superficieMin) parts.push(`≥ ${superficieMin} m²`);
    return parts.join(" · ");
  };

  // Enregistre la recherche dans l'historique ~1,2 s après la dernière
  // modification de filtre (le temps que l'utilisateur "se stabilise" sur
  // des critères), et seulement si au moins un filtre autre que le type de
  // transaction est actif — inutile de garder "parcourir toutes les
  // annonces" dans l'historique.
  useEffect(() => {
    if (skipProchainEnregistrement.current) {
      skipProchainEnregistrement.current = false;
      return;
    }
    const aDesFiltresSignificatifs = Boolean(
      ville || type !== "tous" || debouncedQ || prixMin || prixMax || superficieMin
    );
    if (!aDesFiltresSignificatifs) return;

    const t = setTimeout(() => {
      const criteres: CriteresRecherche = {
        type_transaction: transactionType,
        ville: ville || undefined,
        type_bien: type,
        q: debouncedQ || undefined,
        prix_min: prixMin || undefined,
        prix_max: prixMax || undefined,
        superficie_min: superficieMin || undefined,
        tri,
      };
      enregistrer(buildLabel(), criteres);
    }, 1200);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transactionType, ville, type, debouncedQ, prixMin, prixMax, superficieMin]);

  const handleApplyHistorique = (criteres: CriteresRecherche) => {
    skipProchainEnregistrement.current = true;
    setTransactionType(criteres.type_transaction);
    setVille(criteres.ville ?? "");
    setType(criteres.type_bien ?? "tous");
    setQ(criteres.q ?? "");
    setDebouncedQ(criteres.q ?? "");
    setPrixMin(criteres.prix_min ?? "");
    setPrixMax(criteres.prix_max ?? "");
    setSuperficieMin(criteres.superficie_min ?? "");
    setTri(criteres.tri ?? "pertinence");
    if (criteres.prix_min || criteres.prix_max || criteres.superficie_min) {
      setShowAdvanced(true);
    }
  };


  // Bien en cours de réservation via la modale de paiement instantané
  // (carte/virement) — uniquement pour les locations, voir handleReserve.
  const [reserveBien, setReserveBien] = useState<Bien | null>(null);

  const handleReserve = async (bien: Bien) => {
    // Une offre d'achat (vente) reste une simple demande envoyée au
    // propriétaire, sans paiement immédiat : le paiement anticipé n'a pas
    // de sens pour l'achat d'un bien immobilier dans ce contexte.
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
    // Location : ouvre la modale de réservation + paiement immédiat
    // (carte/virement), avant toute validation du propriétaire.
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

  const handleToggleSimilar = async (bien: Bien) => {
    if (similarFor === bien.id) {
      setSimilarFor(null);
      setSimilarResults(null);
      return;
    }
    setSimilarFor(bien.id);
    setSimilarResults(null);
    setSimilarLoading(true);
    try {
      const res = await api.get<RecommandationResponse>(`/ia/recommandation/${bien.id}?top_n=4`);
      setSimilarResults(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Recommandation temporairement indisponible");
      setSimilarFor(null);
    } finally {
      setSimilarLoading(false);
    }
  };

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">
        Rechercher un bien
      </h1>

      {/* Nav séparant les annonces à louer des annonces à vendre */}
      <div className="mt-4 flex w-fit overflow-hidden rounded-md border border-[var(--color-line)]">
        <button
          type="button"
          onClick={() => setTransactionType("location")}
          className={`px-5 py-2 text-sm font-medium transition-colors ${
            transactionType === "location"
              ? "bg-[var(--color-brass)] text-white"
              : "bg-[var(--color-card)] text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
          }`}
        >
          Louer
        </button>
        <button
          type="button"
          onClick={() => setTransactionType("vente")}
          className={`border-l border-[var(--color-line)] px-5 py-2 text-sm font-medium transition-colors ${
            transactionType === "vente"
              ? "bg-[var(--color-brass)] text-white"
              : "bg-[var(--color-card)] text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
          }`}
        >
          Acheter
        </button>
      </div>

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

      <div className="mt-6 mb-6 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[220px] flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-ink-3)]" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Rechercher (titre, description, quartier…)"
              className="w-full rounded-md border border-[var(--color-line)] py-2 pl-9 pr-3 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>
          <div className="relative min-w-[160px]">
            <input
              value={ville}
              onChange={(e) => setVille(e.target.value)}
              placeholder="Ville (ex. Casablanca)"
              className="w-full rounded-md border border-[var(--color-line)] py-2 px-3 text-sm outline-none focus:border-[var(--color-brass)]"
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
          <select
            value={tri}
            onChange={(e) => setTri(e.target.value as typeof tri)}
            className="rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            title="Trier les résultats"
          >
            <option value="pertinence">Pertinence</option>
            <option value="recent">Plus récents</option>
            <option value="prix_asc">Prix croissant</option>
            <option value="prix_desc">Prix décroissant</option>
          </select>
          <button
            type="button"
            onClick={() => setShowAdvanced((v) => !v)}
            className={`flex items-center gap-1.5 rounded-md border px-3 py-2 text-xs font-medium transition-colors ${
              showAdvanced
                ? "border-[var(--color-brass)] text-[var(--color-brass-deep)]"
                : "border-[var(--color-line)] text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
            }`}
          >
            <SlidersHorizontal size={13} />
            Filtres avancés
          </button>
          <SearchHistoryPanel onApply={handleApplyHistorique} />

          <div className="ml-auto flex items-center gap-3">
            <span className="font-mono text-xs text-[var(--color-ink-3)]">
              {loading ? "Recherche…" : `${biens.length} bien(s) trouvé(s)`}
            </span>
            <div className="flex overflow-hidden rounded-md border border-[var(--color-line)]">
              <button
                type="button"
                onClick={() => setView("liste")}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
                  view === "liste"
                    ? "bg-[var(--color-brass)] text-white"
                    : "text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                }`}
              >
                <LayoutGrid size={13} />
                Liste
              </button>
              <button
                type="button"
                onClick={() => setView("carte")}
                className={`flex items-center gap-1.5 border-l border-[var(--color-line)] px-3 py-1.5 text-xs font-medium transition-colors ${
                  view === "carte"
                    ? "bg-[var(--color-brass)] text-white"
                    : "text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                }`}
              >
                <MapIcon size={13} />
                Carte
              </button>
            </div>
          </div>
        </div>

        {showAdvanced && (
          <div className="mt-3 flex flex-wrap items-end gap-3 border-t border-[var(--color-line)] pt-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
                Prix min (MAD)
              </label>
              <input
                type="number"
                min={0}
                value={prixMin}
                onChange={(e) => setPrixMin(e.target.value)}
                className="w-32 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-sm outline-none focus:border-[var(--color-brass)]"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
                Prix max (MAD)
              </label>
              <input
                type="number"
                min={0}
                value={prixMax}
                onChange={(e) => setPrixMax(e.target.value)}
                className="w-32 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-sm outline-none focus:border-[var(--color-brass)]"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
                Superficie min (m²)
              </label>
              <input
                type="number"
                min={0}
                value={superficieMin}
                onChange={(e) => setSuperficieMin(e.target.value)}
                className="w-32 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-sm outline-none focus:border-[var(--color-brass)]"
              />
            </div>
            {(prixMin || prixMax || superficieMin) && (
              <button
                type="button"
                onClick={() => {
                  setPrixMin("");
                  setPrixMax("");
                  setSuperficieMin("");
                }}
                className="text-xs font-medium text-[var(--color-ink-3)] hover:text-[var(--color-rust)]"
              >
                Réinitialiser
              </button>
            )}
          </div>
        )}
      </div>

      {view === "carte" ? (
        <PropertiesMap biens={biens} onReserve={handleReserve} onContact={handleContact} />
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {biens.map((b) => (
            <div key={b.id}>
              <PropertyCard bien={b} onReserve={handleReserve} onContact={handleContact} />
              <button
                type="button"
                onClick={() => handleToggleSimilar(b)}
                className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-md border border-dashed border-[var(--color-brass)] py-1.5 text-xs font-medium text-[var(--color-brass-deep)] hover:bg-[#f4e9df]/40"
              >
                <Sparkles size={12} />
                {similarFor === b.id ? "Masquer les biens similaires" : "Voir des biens similaires"}
              </button>
              {similarFor === b.id && similarLoading && (
                <p className="mt-2 text-xs text-[var(--color-ink-3)]">Recherche en cours…</p>
              )}
              {similarFor === b.id && similarResults && (
                <SimilarPropertiesPanel
                  items={similarResults.resultats}
                  sourceCatalogue={similarResults.source_catalogue}
                />
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && biens.length === 0 && (
        <p className="mt-8 text-center text-sm text-[var(--color-ink-3)]">
          Aucun bien disponible pour ces critères pour le moment.
        </p>
      )}

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

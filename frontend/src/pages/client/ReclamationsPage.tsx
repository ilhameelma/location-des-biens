import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Flag, Search, X } from "lucide-react";
import { api } from "../../lib/api";
import type { Bien, Reclamation } from "../../types";
import StatusBadge from "../../components/ui/StatusBadge";

const TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: "annonce_trompeuse", label: "Annonce trompeuse" },
  { value: "prix_incorrect", label: "Prix incorrect / non respecté" },
  { value: "bien_indisponible", label: "Bien déjà indisponible" },
  { value: "comportement_proprietaire", label: "Comportement du propriétaire" },
  { value: "autre", label: "Autre" },
];

export default function ReclamationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const prefilledBienId = searchParams.get("bien_id");
  const prefilledTitre = searchParams.get("titre");

  const [reclamations, setReclamations] = useState<Reclamation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Formulaire de création
  const [showForm, setShowForm] = useState(Boolean(prefilledBienId));
  const [selectedBien, setSelectedBien] = useState<Bien | null>(null);
  const [bienQuery, setBienQuery] = useState("");
  const [bienResults, setBienResults] = useState<Bien[]>([]);
  const [typeReclamation, setTypeReclamation] = useState(TYPE_OPTIONS[0].value);
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchReclamations = () => {
    setLoading(true);
    api
      .get<Reclamation[]>("/reclamations/me")
      .then(setReclamations)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchReclamations, []);

  // Si on arrive depuis le bouton "Signaler cette annonce" d'une fiche bien,
  // on pré-sélectionne directement le bien concerné.
  useEffect(() => {
    if (prefilledBienId) {
      setSelectedBien({ id: prefilledBienId, titre: prefilledTitre ?? "Annonce sélectionnée" } as Bien);
      setShowForm(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefilledBienId]);

  // Recherche d'un bien par titre/ville (texte libre, débouncée) quand
  // l'utilisateur ouvre le formulaire sans venir d'une fiche détaillée.
  useEffect(() => {
    if (!bienQuery || selectedBien) {
      setBienResults([]);
      return;
    }
    const t = setTimeout(() => {
      api
        .get<Bien[]>(`/biens?q=${encodeURIComponent(bienQuery)}`)
        .then((res) => setBienResults(res.slice(0, 6)))
        .catch(() => setBienResults([]));
    }, 350);
    return () => clearTimeout(t);
  }, [bienQuery, selectedBien]);

  const resetForm = () => {
    setSelectedBien(null);
    setBienQuery("");
    setBienResults([]);
    setTypeReclamation(TYPE_OPTIONS[0].value);
    setDescription("");
    setSearchParams({});
  };

  const handleSubmit = async () => {
    if (!description.trim()) {
      setError("Merci de décrire le problème rencontré.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/reclamations", {
        bien_id: selectedBien?.id ?? null,
        type_reclamation: typeReclamation,
        description: description.trim(),
      });
      setMessage("Votre réclamation a bien été envoyée. Notre équipe va l'examiner.");
      setTimeout(() => setMessage(null), 5000);
      resetForm();
      setShowForm(false);
      fetchReclamations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d'envoyer la réclamation");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">
          Mes réclamations
        </h1>
        {!showForm && (
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)]"
          >
            <Flag size={15} />
            Nouvelle réclamation
          </button>
        )}
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

      {showForm && (
        <div className="mt-6 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-5">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-lg text-[var(--color-ink)]">Signaler une annonce</h2>
            <button
              type="button"
              onClick={() => {
                setShowForm(false);
                resetForm();
              }}
              className="text-[var(--color-ink-3)] hover:text-[var(--color-ink)]"
              aria-label="Fermer"
            >
              <X size={18} />
            </button>
          </div>

          {/* Sélection du bien concerné */}
          <div className="mt-4">
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--color-ink-3)]">
              Annonce concernée (optionnel)
            </label>
            {selectedBien ? (
              <div className="flex items-center justify-between rounded-md border border-[var(--color-line)] bg-[var(--color-paper-2)] px-3 py-2 text-sm">
                <span className="text-[var(--color-ink)]">{selectedBien.titre}</span>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedBien(null);
                    setSearchParams({});
                  }}
                  className="text-xs text-[var(--color-ink-3)] hover:text-[var(--color-rust)]"
                >
                  Changer
                </button>
              </div>
            ) : (
              <div className="relative">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-ink-3)]" />
                <input
                  value={bienQuery}
                  onChange={(e) => setBienQuery(e.target.value)}
                  placeholder="Rechercher par titre, ville…"
                  className="w-full rounded-md border border-[var(--color-line)] py-2 pl-9 pr-3 text-sm outline-none focus:border-[var(--color-brass)]"
                />
                {bienResults.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full rounded-md border border-[var(--color-line)] bg-[var(--color-card)] shadow-md">
                    {bienResults.map((b) => (
                      <button
                        key={b.id}
                        type="button"
                        onClick={() => {
                          setSelectedBien(b);
                          setBienQuery("");
                          setBienResults([]);
                        }}
                        className="block w-full px-3 py-2 text-left text-sm hover:bg-[var(--color-paper-2)]"
                      >
                        {b.titre} <span className="text-[var(--color-ink-3)]">— {b.ville}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Type de réclamation */}
          <div className="mt-4">
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--color-ink-3)]">
              Motif
            </label>
            <select
              value={typeReclamation}
              onChange={(e) => setTypeReclamation(e.target.value)}
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            >
              {TYPE_OPTIONS.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div className="mt-4">
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--color-ink-3)]">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              placeholder="Décrivez le problème rencontré…"
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            className="mt-4 rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
          >
            {submitting ? "Envoi…" : "Envoyer la réclamation"}
          </button>
        </div>
      )}

      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && reclamations.length === 0 && !error && (
        <p className="mt-6 text-sm text-[var(--color-ink-3)]">
          Vous n'avez déposé aucune réclamation.
        </p>
      )}

      <div className="mt-6 space-y-3">
        {reclamations.map((r) => (
          <div key={r.id} className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4">
            <div className="flex items-center justify-between">
              <span className="font-medium text-[var(--color-ink)]">
                {TYPE_OPTIONS.find((t) => t.value === r.type_reclamation)?.label ?? r.type_reclamation}
              </span>
              <StatusBadge status={r.statut} />
            </div>
            {r.bien_titre && (
              <p className="mt-1 text-xs text-[var(--color-ink-3)]">Annonce : {r.bien_titre}</p>
            )}
            <p className="mt-1 text-sm text-[var(--color-ink-2)]">{r.description}</p>
            <p className="mt-2 font-mono text-xs text-[var(--color-ink-3)]">
              Envoyée le {new Date(r.date_creation).toLocaleDateString("fr-MA")}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

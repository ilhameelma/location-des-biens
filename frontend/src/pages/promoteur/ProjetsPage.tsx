import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Plus, X, FolderKanban, MapPin, Layers } from "lucide-react";
import LocationPicker from "../../components/map/LocationPicker";
import { api } from "../../lib/api";
import type { ProjetImmobilier, TypeBien, StatutProjet } from "../../types";

const TYPES: TypeBien[] = ["appartement", "maison", "villa", "bureau", "magasin", "garage", "terrain"];

const STATUT_LABEL: Record<StatutProjet, string> = {
  en_construction: "En construction",
  livre: "Livré",
  termine: "Terminé",
};

const STATUT_STYLE: Record<StatutProjet, string> = {
  en_construction: "bg-[var(--color-brass-bg)] text-[var(--color-brass)]",
  livre: "bg-green-100 text-green-700",
  termine: "bg-[var(--color-paper-2)] text-[var(--color-ink-2)]",
};

export default function ProjetsPage() {
  const [projets, setProjets] = useState<ProjetImmobilier[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    nom: "",
    description: "",
    type_bien: "appartement" as TypeBien,
    ville: "",
    adresse: "",
    latitude: null as number | null,
    longitude: null as number | null,
    date_livraison_prevue: "",
  });

  const fetchProjets = () => {
    setLoading(true);
    api
      .get<ProjetImmobilier[]>("/projets/me")
      .then(setProjets)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchProjets, []);

  const resetForm = () =>
    setForm({
      nom: "",
      description: "",
      type_bien: "appartement",
      ville: "",
      adresse: "",
      latitude: null,
      longitude: null,
      date_livraison_prevue: "",
    });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.post<ProjetImmobilier>("/projets", {
        nom: form.nom,
        description: form.description || null,
        type_bien: form.type_bien,
        ville: form.ville,
        adresse: form.adresse,
        latitude: form.latitude,
        longitude: form.longitude,
        date_livraison_prevue: form.date_livraison_prevue || null,
      });
      setShowForm(false);
      resetForm();
      fetchProjets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de créer ce projet");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Mes projets</h1>
        <button
          type="button"
          onClick={() => setShowForm((s) => !s)}
          className="flex items-center gap-2 rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)]"
        >
          {showForm ? <X size={16} /> : <Plus size={16} />}
          {showForm ? "Annuler" : "Nouveau projet"}
        </button>
      </div>

      <p className="mt-2 text-sm text-[var(--color-ink-3)]">
        Un projet regroupe plusieurs lots (ex. "Résidence Al Manar", 24
        appartements). Créez le projet ici, puis ouvrez-le pour y publier vos
        lots un par un.
      </p>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="mt-6 grid grid-cols-1 gap-3 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-5 sm:grid-cols-2"
        >
          <div className="sm:col-span-2">
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Nom du projet</label>
            <input
              required
              value={form.nom}
              onChange={(e) => setForm({ ...form, nom: e.target.value })}
              placeholder='ex. "Résidence Al Manar"'
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Type de lots</label>
            <select
              value={form.type_bien}
              onChange={(e) => setForm({ ...form, type_bien: e.target.value as TypeBien })}
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            >
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
              Livraison prévue (optionnel)
            </label>
            <input
              type="date"
              value={form.date_livraison_prevue}
              onChange={(e) => setForm({ ...form, date_livraison_prevue: e.target.value })}
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Ville</label>
            <input
              required
              value={form.ville}
              onChange={(e) => setForm({ ...form, ville: e.target.value })}
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Adresse</label>
            <input
              required
              value={form.adresse}
              onChange={(e) => setForm({ ...form, adresse: e.target.value })}
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>
          <LocationPicker
            latitude={form.latitude}
            longitude={form.longitude}
            ville={form.ville}
            adresse={form.adresse}
            onChange={(lat, lng) => setForm((f) => ({ ...f, latitude: lat, longitude: lng }))}
          />
          <div className="sm:col-span-2">
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
              Description (optionnel)
            </label>
            <textarea
              rows={2}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
            >
              {submitting ? "Création…" : "Créer le projet"}
            </button>
          </div>
        </form>
      )}

      <h2 className="mt-10 mb-4 font-display text-lg text-[var(--color-ink)]">Projets</h2>
      {loading && <p className="text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && projets.length === 0 && (
        <p className="text-sm text-[var(--color-ink-3)]">Aucun projet créé pour le moment.</p>
      )}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projets.map((p) => (
          <Link
            key={p.id}
            to={`/promoteur/projets/${p.id}`}
            className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4 transition hover:border-[var(--color-brass)]"
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-display text-base text-[var(--color-ink)]">{p.nom}</h3>
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${STATUT_STYLE[p.statut]}`}>
                {STATUT_LABEL[p.statut]}
              </span>
            </div>
            <p className="mt-1 flex items-center gap-1 text-xs text-[var(--color-ink-3)]">
              <MapPin size={12} />
              {p.ville}
            </p>
            <p className="mt-2 flex items-center gap-1 text-xs text-[var(--color-ink-2)]">
              <Layers size={12} />
              {p.nb_lots} lot{p.nb_lots > 1 ? "s" : ""} — {p.nb_lots_disponibles} disponible
              {p.nb_lots_disponibles > 1 ? "s" : ""}
            </p>
            {p.prix_min != null && (
              <p className="mt-1 text-xs text-[var(--color-ink-3)]">
                {p.prix_min === p.prix_max
                  ? `${p.prix_min.toLocaleString("fr-FR")} MAD`
                  : `${p.prix_min.toLocaleString("fr-FR")} – ${p.prix_max?.toLocaleString("fr-FR")} MAD`}
              </p>
            )}
            <p className="mt-3 flex items-center gap-1 text-xs font-medium text-[var(--color-brass)]">
              <FolderKanban size={12} />
              Gérer les lots
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}

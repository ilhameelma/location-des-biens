import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Plus, X, Upload, Trash2 } from "lucide-react";
import PropertyCard from "../../components/ui/PropertyCard";
import LocationPicker from "../../components/map/LocationPicker";
import EstimationWidget from "../../components/ia/EstimationWidget";
import { api, formatErrorDetail } from "../../lib/api";
import type { Bien, ProjetImmobilier, TypeBien, TypeTransaction, StatutProjet } from "../../types";

const TYPES: TypeBien[] = ["appartement", "maison", "villa", "bureau", "magasin", "garage", "terrain"];

const STATUTS: { value: StatutProjet; label: string }[] = [
  { value: "en_construction", label: "En construction" },
  { value: "livre", label: "Livré" },
  { value: "termine", label: "Terminé" },
];

export default function ProjetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [projet, setProjet] = useState<ProjetImmobilier | null>(null);
  const [lots, setLots] = useState<Bien[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [savingStatut, setSavingStatut] = useState(false);

  const [form, setForm] = useState({
    titre: "",
    description: "",
    type_bien: "appartement" as TypeBien,
    type_transaction: "vente" as TypeTransaction,
    ville: "",
    adresse: "",
    prix: "",
    superficie: "",
    nb_pieces: "",
    latitude: null as number | null,
    longitude: null as number | null,
  });

  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchAll = () => {
    if (!id) return;
    setLoading(true);
    Promise.all([
      api.get<ProjetImmobilier>(`/projets/${id}`),
      api.get<Bien[]>(`/projets/${id}/lots`),
    ])
      .then(([p, l]) => {
        setProjet(p);
        setLots(l);
        // Pré-remplit le formulaire de nouveau lot avec la ville/adresse/position
        // du projet, pour éviter de les ressaisir à chaque lot.
        setForm((f) => ({
          ...f,
          type_bien: p.type_bien,
          ville: p.ville,
          adresse: p.adresse,
          latitude: p.latitude ?? null,
          longitude: p.longitude ?? null,
        }));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchAll, [id]);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const newFiles = Array.from(files);
    const combined = [...selectedImages, ...newFiles].slice(0, 5);
    setSelectedImages(combined);
    const newPreviews = newFiles.map((file) => URL.createObjectURL(file));
    setPreviewUrls((prev) => [...prev, ...newPreviews].slice(0, 5));
  };

  const removeImage = (index: number) => {
    setSelectedImages((prev) => prev.filter((_, i) => i !== index));
    setPreviewUrls((prev) => {
      URL.revokeObjectURL(prev[index]);
      return prev.filter((_, i) => i !== index);
    });
  };

  const resetForm = () => {
    setForm((f) => ({
      ...f,
      titre: "",
      description: "",
      prix: "",
      superficie: "",
      nb_pieces: "",
    }));
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
    setSelectedImages([]);
    setPreviewUrls([]);
  };

  const handleCreateLot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setSubmitting(true);
    setError(null);
    try {
      const bienRes = await api.post<Bien>("/biens", {
        titre: form.titre,
        description: form.description || null,
        type_bien: form.type_bien,
        type_transaction: form.type_transaction,
        ville: form.ville,
        adresse: form.adresse,
        prix: Number(form.prix),
        superficie: form.superficie ? Number(form.superficie) : null,
        nb_pieces: form.nb_pieces ? Number(form.nb_pieces) : null,
        latitude: form.latitude,
        longitude: form.longitude,
        projet_id: id,
      });

      if (selectedImages.length > 0 && bienRes.id) {
        const formData = new FormData();
        selectedImages.forEach((file, idx) => {
          formData.append("photos", file);
          formData.append("ordres", String(idx));
        });
        formData.append("bien_id", bienRes.id);

        const token = localStorage.getItem("smartrent_token");
        const res = await fetch(`http://localhost:8000/api/biens/${bienRes.id}/photos`, {
          method: "POST",
          headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
          body: formData,
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(formatErrorDetail(body.detail, res.status) || `Erreur upload photos (${res.status})`);
        }
      }

      setShowForm(false);
      resetForm();
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de publier ce lot");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteLot = async (bien: Bien) => {
    const confirmed = window.confirm(
      `Supprimer définitivement le lot « ${bien.titre} » ? Cette action est irréversible.`
    );
    if (!confirmed) return;
    setDeleting(bien.id);
    setError(null);
    try {
      await api.del(`/biens/${bien.id}`);
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de supprimer ce lot");
    } finally {
      setDeleting(null);
    }
  };

  const handleStatutChange = async (statut: StatutProjet) => {
    if (!id) return;
    setSavingStatut(true);
    setError(null);
    try {
      const updated = await api.patch<ProjetImmobilier>(`/projets/${id}`, { statut });
      setProjet(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de mettre à jour le statut");
    } finally {
      setSavingStatut(false);
    }
  };

  const handleDeleteProjet = async () => {
    if (!id || !projet) return;
    if (lots.length > 0) {
      window.alert(
        "Ce projet contient encore des lots. Supprimez-les d'abord depuis cette page avant de supprimer le projet."
      );
      return;
    }
    const confirmed = window.confirm(`Supprimer définitivement le projet « ${projet.nom} » ?`);
    if (!confirmed) return;
    try {
      await api.del(`/projets/${id}`);
      navigate("/promoteur/projets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de supprimer ce projet");
    }
  };

  if (loading) return <p className="text-sm text-[var(--color-ink-3)]">Chargement…</p>;
  if (!projet) return <p className="text-sm text-[var(--color-rust)]">Projet introuvable.</p>;

  return (
    <div>
      <Link
        to="/promoteur/projets"
        className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--color-ink-2)] hover:text-[var(--color-brass)]"
      >
        <ArrowLeft size={15} />
        Retour à mes projets
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">{projet.nom}</h1>
          <p className="mt-1 text-sm text-[var(--color-ink-3)]">
            {projet.ville} — {projet.adresse}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={projet.statut}
            disabled={savingStatut}
            onChange={(e) => handleStatutChange(e.target.value as StatutProjet)}
            className="rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
          >
            {STATUTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={handleDeleteProjet}
            className="flex items-center gap-1.5 rounded-md border border-[var(--color-rust)]/40 px-3 py-2 text-xs font-medium text-[var(--color-rust)] hover:bg-[var(--color-rust-bg)]"
          >
            <Trash2 size={13} />
            Supprimer le projet
          </button>
        </div>
      </div>

      {projet.description && (
        <p className="mt-3 max-w-2xl text-sm text-[var(--color-ink-2)]">{projet.description}</p>
      )}

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}

      <div className="mt-8 flex items-center justify-between">
        <h2 className="font-display text-lg text-[var(--color-ink)]">
          Lots ({lots.length})
        </h2>
        <button
          type="button"
          onClick={() => setShowForm((s) => !s)}
          className="flex items-center gap-2 rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)]"
        >
          {showForm ? <X size={16} /> : <Plus size={16} />}
          {showForm ? "Annuler" : "Ajouter un lot"}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreateLot}
          className="mt-4 grid grid-cols-1 gap-3 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-5 sm:grid-cols-2"
        >
          <div className="sm:col-span-2">
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
              Titre du lot
            </label>
            <input
              required
              value={form.titre}
              onChange={(e) => setForm({ ...form, titre: e.target.value })}
              placeholder='ex. "Appartement 3B — 2ème étage"'
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Type</label>
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
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Transaction</label>
            <div className="flex overflow-hidden rounded-md border border-[var(--color-line)]">
              <button
                type="button"
                onClick={() => setForm({ ...form, type_transaction: "vente" })}
                className={`flex-1 py-2 text-sm font-medium transition-colors ${
                  form.type_transaction === "vente"
                    ? "bg-[var(--color-brass)] text-white"
                    : "text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                }`}
              >
                Vendre
              </button>
              <button
                type="button"
                onClick={() => setForm({ ...form, type_transaction: "location" })}
                className={`flex-1 border-l border-[var(--color-line)] py-2 text-sm font-medium transition-colors ${
                  form.type_transaction === "location"
                    ? "bg-[var(--color-brass)] text-white"
                    : "text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                }`}
              >
                Louer
              </button>
            </div>
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
          <div>
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

          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Superficie (m²)</label>
            <input
              type="number"
              value={form.superficie}
              onChange={(e) => setForm({ ...form, superficie: e.target.value })}
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Nb. pièces</label>
            <input
              type="number"
              value={form.nb_pieces}
              onChange={(e) => setForm({ ...form, nb_pieces: e.target.value })}
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>

          <EstimationWidget
            ville={form.ville}
            superficie={form.superficie}
            nb_pieces={form.nb_pieces}
            type_bien={form.type_bien}
            type_transaction={form.type_transaction}
            onApply={(prix) => setForm((f) => ({ ...f, prix: String(prix) }))}
          />

          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
              Prix {form.type_transaction === "vente" ? "(MAD)" : "(MAD/mois)"}
            </label>
            <input
              required
              type="number"
              value={form.prix}
              onChange={(e) => setForm({ ...form, prix: e.target.value })}
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
            />
          </div>
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
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
              Photos du lot (max. 5)
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={handleImageSelect}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={selectedImages.length >= 5}
              className="flex w-full items-center justify-center gap-2 rounded-md border-2 border-dashed border-[var(--color-line)] px-4 py-6 text-sm text-[var(--color-ink-2)] transition hover:border-[var(--color-brass)] hover:text-[var(--color-brass)] disabled:opacity-40"
            >
              <Upload size={18} />
              {selectedImages.length === 0
                ? "Cliquez pour sélectionner des images"
                : `Ajouter d'autres images (${selectedImages.length}/5)`}
            </button>
            {previewUrls.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-3">
                {previewUrls.map((url, idx) => (
                  <div key={idx} className="group relative h-20 w-20 overflow-hidden rounded-md border border-[var(--color-line)]">
                    <img src={url} alt={`Aperçu ${idx + 1}`} className="h-full w-full object-cover" />
                    <button
                      type="button"
                      onClick={() => removeImage(idx)}
                      className="absolute right-0.5 top-0.5 rounded-full bg-black/60 p-0.5 text-white opacity-0 transition group-hover:opacity-100"
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
            >
              {submitting ? "Publication…" : "Publier ce lot"}
            </button>
          </div>
        </form>
      )}

      {lots.length === 0 ? (
        <p className="mt-4 text-sm text-[var(--color-ink-3)]">Aucun lot publié pour ce projet pour le moment.</p>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {lots.map((l) => (
            <div key={l.id}>
              <PropertyCard bien={l} />
              <button
                type="button"
                onClick={() => handleDeleteLot(l)}
                disabled={deleting === l.id}
                className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-md border border-[var(--color-rust)]/40 py-1.5 text-xs font-medium text-[var(--color-rust)] hover:bg-[var(--color-rust-bg)] disabled:opacity-50"
              >
                <Trash2 size={13} />
                {deleting === l.id ? "Suppression…" : "Supprimer ce lot"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

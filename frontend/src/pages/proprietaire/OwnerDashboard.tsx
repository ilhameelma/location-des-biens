import { useEffect, useState, useRef } from "react";
import { Building2, Wallet, FileSignature, Plus, X, Upload } from "lucide-react";
import StatCard from "../../components/ui/StatCard";
import PropertyCard from "../../components/ui/PropertyCard";
import EstimationWidget from "../../components/ia/EstimationWidget";
import { api } from "../../lib/api";
import type { Bien, TypeBien } from "../../types";

const TYPES: TypeBien[] = ["appartement", "maison", "bureau", "magasin", "garage", "terrain"];

export default function OwnerDashboard() {
  const [biens, setBiens] = useState<Bien[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    titre: "",
    description: "",
    type_bien: "appartement" as TypeBien,
    ville: "",
    adresse: "",
    prix: "",
    superficie: "",
    nb_pieces: "",
  });

  // --- Gestion des images ---
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchBiens = () => {
    setLoading(true);
    api
      .get<Bien[]>("/biens/me/annonces")
      .then(setBiens)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchBiens();
  }, []);

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
    setForm({
      titre: "",
      description: "",
      type_bien: "appartement",
      ville: "",
      adresse: "",
      prix: "",
      superficie: "",
      nb_pieces: "",
    });
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
    setSelectedImages([]);
    setPreviewUrls([]);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      // Étape 1 : créer le bien
      const bienRes = await api.post<Bien>("/biens", {
        titre: form.titre,
        description: form.description || null,
        type_bien: form.type_bien,
        ville: form.ville,
        adresse: form.adresse,
        prix: Number(form.prix),
        superficie: form.superficie ? Number(form.superficie) : null,
        nb_pieces: form.nb_pieces ? Number(form.nb_pieces) : null,
      });

      const bienId = bienRes.id;

      if (!bienId) {
        throw new Error("Le bien a été créé mais l'identifiant est manquant");
      }

      // Étape 2 : uploader les images avec fetch natif (pas api.post)
      // car FormData nécessite un Content-Type auto-généré avec boundary
      if (selectedImages.length > 0) {
        const formData = new FormData();
        selectedImages.forEach((file, idx) => {
          formData.append("photos", file);
          formData.append("ordres", String(idx));
        });
        formData.append("bien_id", bienId);

        const token = localStorage.getItem("smartrent_token");
        const res = await fetch(`http://localhost:8000/api/biens/${bienId}/photos`, {
          method: "POST",
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            // NE PAS mettre "Content-Type" ici — le navigateur le génère avec le boundary
          },
          body: formData,
        });

        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail ?? `Erreur upload photos (${res.status})`);
        }
      }

      setShowForm(false);
      resetForm();
      fetchBiens();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de publier cette annonce");
    } finally {
      setSubmitting(false);
    }
  };

  const loues = biens.filter((b) => b.statut === "loue").length;

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Mes biens</h1>
        <button
          type="button"
          onClick={() => setShowForm((s) => !s)}
          className="flex items-center gap-2 rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)]"
        >
          {showForm ? <X size={16} /> : <Plus size={16} />}
          {showForm ? "Annuler" : "Publier une annonce"}
        </button>
      </div>

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
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Titre</label>
            <input
              required
              value={form.titre}
              onChange={(e) => setForm({ ...form, titre: e.target.value })}
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
            onApply={(prix) => setForm((f) => ({ ...f, prix: String(prix) }))}
          />

          <div>
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Prix (MAD/mois)</label>
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

          {/* --- Champ d'upload d'images --- */}
          <div className="sm:col-span-2">
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
              Photos du bien (max. 5)
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
              className="flex w-full items-center justify-center gap-2 rounded-md border-2 border-dashed border-[var(--color-line)] px-4 py-6 text-sm text-[var(--color-ink-2)] transition hover:border-[var(--color-brass)] hover:text-[var(--color-brass)] disabled:opacity-40 disabled:hover:border-[var(--color-line)]"
            >
              <Upload size={18} />
              {selectedImages.length === 0
                ? "Cliquez pour sélectionner des images depuis votre machine"
                : `Ajouter d'autres images (${selectedImages.length}/5)`}
            </button>

            {previewUrls.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-3">
                {previewUrls.map((url, idx) => (
                  <div key={idx} className="group relative h-20 w-20 overflow-hidden rounded-md border border-[var(--color-line)]">
                    <img
                      src={url}
                      alt={`Aperçu ${idx + 1}`}
                      className="h-full w-full object-cover"
                    />
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
              {submitting ? "Publication…" : "Publier l'annonce"}
            </button>
            <p className="mt-2 text-xs text-[var(--color-ink-3)]">
              L'annonce sera créée avec le statut « disponible ». Les images seront stockées
              sur MinIO une fois l'intégration terminée (étape 7).
            </p>
          </div>
        </form>
      )}

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Biens publiés" value={String(biens.length)} icon={Building2} />
        <StatCard label="Biens loués" value={String(loues)} icon={FileSignature} />
        <StatCard label="Revenus estimés" value={`${loues > 0 ? "voir Paiements" : "0"}`} icon={Wallet} />
      </div>

      <h2 className="mt-10 mb-4 font-display text-lg text-[var(--color-ink)]">Annonces</h2>
      {loading && <p className="text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && biens.length === 0 && (
        <p className="text-sm text-[var(--color-ink-3)]">
          Aucune annonce publiée pour le moment. Utilise le bouton ci-dessus.
        </p>
      )}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {biens.map((b) => (
          <PropertyCard key={b.id} bien={b} />
        ))}
      </div>
    </div>
  );
}
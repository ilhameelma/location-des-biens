import { useEffect, useState, useRef } from "react";
import { Building2, Wallet, FileSignature, Plus, X, Upload, Pencil, Trash2 } from "lucide-react";
import StatCard from "../../components/ui/StatCard";
import PropertyCard from "../../components/ui/PropertyCard";
import EstimationWidget from "../../components/ia/EstimationWidget";
import LocationPicker from "../../components/map/LocationPicker";
import { api, formatErrorDetail } from "../../lib/api";
import type { Bien, TypeBien, TypeTransaction } from "../../types";

const TYPES: TypeBien[] = ["appartement", "maison", "villa", "bureau", "magasin", "garage", "terrain"];

export default function OwnerDashboard() {
  const [biens, setBiens] = useState<Bien[]>([]);
  const [filtreTransaction, setFiltreTransaction] = useState<"tous" | TypeTransaction>("tous");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    titre: "",
    description: "",
    type_bien: "appartement" as TypeBien,
    type_transaction: "location" as TypeTransaction,
    ville: "",
    adresse: "",
    prix: "",
    superficie: "",
    nb_pieces: "",
    latitude: null as number | null,
    longitude: null as number | null,
  });

  // --- Gestion des images ---
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [previewUrls, setPreviewUrls] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Édition de la position d'un bien déjà publié (rattrapage géolocalisation) ---
  const [editingLocationFor, setEditingLocationFor] = useState<string | null>(null);
  const [editLat, setEditLat] = useState<number | null>(null);
  const [editLng, setEditLng] = useState<number | null>(null);
  const [savingLocation, setSavingLocation] = useState(false);

  // --- Édition complète d'une annonce existante ---
  const [editingBienId, setEditingBienId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({
    titre: "",
    description: "",
    type_bien: "appartement" as TypeBien,
    type_transaction: "location" as TypeTransaction,
    ville: "",
    adresse: "",
    prix: "",
    superficie: "",
    nb_pieces: "",
  });
  const [savingEdit, setSavingEdit] = useState(false);

  // --- Suppression d'une annonce ---
  const [deletingBienId, setDeletingBienId] = useState<string | null>(null);

  const fetchBiens = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filtreTransaction !== "tous") params.set("type_transaction", filtreTransaction);
    api
      .get<Bien[]>(`/biens/me/annonces?${params.toString()}`)
      .then(setBiens)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchBiens();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtreTransaction]);

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
      type_transaction: "location",
      ville: "",
      adresse: "",
      prix: "",
      superficie: "",
      nb_pieces: "",
      latitude: null,
      longitude: null,
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
        type_transaction: form.type_transaction,
        ville: form.ville,
        adresse: form.adresse,
        prix: Number(form.prix),
        superficie: form.superficie ? Number(form.superficie) : null,
        nb_pieces: form.nb_pieces ? Number(form.nb_pieces) : null,
        latitude: form.latitude,
        longitude: form.longitude,
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
          throw new Error(formatErrorDetail(body.detail, res.status) || `Erreur upload photos (${res.status})`);
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

  const openLocationEditor = (bien: Bien) => {
    setEditingBienId(null); // les deux éditeurs ne s'affichent pas en même temps
    setEditingLocationFor(bien.id);
    setEditLat(bien.latitude ?? null);
    setEditLng(bien.longitude ?? null);
  };

  const cancelLocationEditor = () => {
    setEditingLocationFor(null);
    setEditLat(null);
    setEditLng(null);
  };

  const saveLocation = async (bienId: string) => {
    if (editLat == null || editLng == null) return;
    setSavingLocation(true);
    setError(null);
    try {
      await api.patch<Bien>(`/biens/${bienId}`, { latitude: editLat, longitude: editLng });
      cancelLocationEditor();
      fetchBiens();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d'enregistrer la position");
    } finally {
      setSavingLocation(false);
    }
  };

  // --- Édition complète d'une annonce ---
  const openEdit = (bien: Bien) => {
    setEditingLocationFor(null); // les deux éditeurs ne s'affichent pas en même temps
    setEditingBienId(bien.id);
    setEditForm({
      titre: bien.titre,
      description: bien.description ?? "",
      type_bien: bien.type_bien,
      type_transaction: bien.type_transaction,
      ville: bien.ville,
      adresse: bien.adresse,
      prix: String(bien.prix),
      superficie: bien.superficie != null ? String(bien.superficie) : "",
      nb_pieces: bien.nb_pieces != null ? String(bien.nb_pieces) : "",
    });
  };

  const cancelEdit = () => setEditingBienId(null);

  const handleUpdate = async (e: React.FormEvent, bienId: string) => {
    e.preventDefault();
    setSavingEdit(true);
    setError(null);
    try {
      await api.patch<Bien>(`/biens/${bienId}`, {
        titre: editForm.titre,
        description: editForm.description || null,
        type_bien: editForm.type_bien,
        type_transaction: editForm.type_transaction,
        ville: editForm.ville,
        adresse: editForm.adresse,
        prix: Number(editForm.prix),
        superficie: editForm.superficie ? Number(editForm.superficie) : null,
        nb_pieces: editForm.nb_pieces ? Number(editForm.nb_pieces) : null,
      });
      setEditingBienId(null);
      fetchBiens();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de modifier cette annonce");
    } finally {
      setSavingEdit(false);
    }
  };

  // --- Suppression d'une annonce ---
  const handleDelete = async (bien: Bien) => {
    const confirmed = window.confirm(
      `Supprimer définitivement « ${bien.titre} » ? Cette action est irréversible : l'annonce et ses photos seront supprimées.`
    );
    if (!confirmed) return;

    setDeletingBienId(bien.id);
    setError(null);
    try {
      await api.del(`/biens/${bien.id}`);
      fetchBiens();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de supprimer cette annonce");
    } finally {
      setDeletingBienId(null);
    }
  };

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

      <div className="mt-4 flex w-fit overflow-hidden rounded-md border border-[var(--color-line)]">
        {(["tous", "location", "vente"] as const).map((v) => (
          <button
            key={v}
            type="button"
            onClick={() => setFiltreTransaction(v)}
            className={`px-4 py-1.5 text-sm font-medium transition-colors ${
              v !== "tous" ? "border-l border-[var(--color-line)]" : ""
            } ${
              filtreTransaction === v
                ? "bg-[var(--color-brass)] text-white"
                : "bg-[var(--color-card)] text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
            }`}
          >
            {v === "tous" ? "Tous" : v === "location" ? "À louer" : "À vendre"}
          </button>
        ))}
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
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
              Transaction
            </label>
            <div className="flex overflow-hidden rounded-md border border-[var(--color-line)]">
              <button
                type="button"
                onClick={() => setForm({ ...form, type_transaction: "location" })}
                className={`flex-1 py-2 text-sm font-medium transition-colors ${
                  form.type_transaction === "location"
                    ? "bg-[var(--color-brass)] text-white"
                    : "text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                }`}
              >
                Louer
              </button>
              <button
                type="button"
                onClick={() => setForm({ ...form, type_transaction: "vente" })}
                className={`flex-1 border-l border-[var(--color-line)] py-2 text-sm font-medium transition-colors ${
                  form.type_transaction === "vente"
                    ? "bg-[var(--color-brass)] text-white"
                    : "text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                }`}
              >
                Vendre
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
              L'annonce sera créée avec le statut « disponible ». Pensez à indiquer la
              position sur la carte ci-dessus pour qu'elle apparaisse en vue Carte côté client.
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
          <div key={b.id}>
            <PropertyCard bien={b} />

            {editingBienId === b.id ? (
              <form
                onSubmit={(e) => handleUpdate(e, b.id)}
                className="mt-2 grid grid-cols-1 gap-3 rounded-md border border-[var(--color-line)] bg-[var(--color-card)] p-4 sm:grid-cols-2"
              >
                <div className="sm:col-span-2">
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Titre</label>
                  <input
                    required
                    value={editForm.titre}
                    onChange={(e) => setEditForm({ ...editForm, titre: e.target.value })}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Type</label>
                  <select
                    value={editForm.type_bien}
                    onChange={(e) => setEditForm({ ...editForm, type_bien: e.target.value as TypeBien })}
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
                      onClick={() => setEditForm({ ...editForm, type_transaction: "location" })}
                      className={`flex-1 py-2 text-sm font-medium transition-colors ${
                        editForm.type_transaction === "location"
                          ? "bg-[var(--color-brass)] text-white"
                          : "text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                      }`}
                    >
                      Louer
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditForm({ ...editForm, type_transaction: "vente" })}
                      className={`flex-1 border-l border-[var(--color-line)] py-2 text-sm font-medium transition-colors ${
                        editForm.type_transaction === "vente"
                          ? "bg-[var(--color-brass)] text-white"
                          : "text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                      }`}
                    >
                      Vendre
                    </button>
                  </div>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Ville</label>
                  <input
                    required
                    value={editForm.ville}
                    onChange={(e) => setEditForm({ ...editForm, ville: e.target.value })}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
                    Prix {editForm.type_transaction === "vente" ? "(MAD)" : "(MAD/mois)"}
                  </label>
                  <input
                    required
                    type="number"
                    value={editForm.prix}
                    onChange={(e) => setEditForm({ ...editForm, prix: e.target.value })}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Adresse</label>
                  <input
                    required
                    value={editForm.adresse}
                    onChange={(e) => setEditForm({ ...editForm, adresse: e.target.value })}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Superficie (m²)</label>
                  <input
                    type="number"
                    value={editForm.superficie}
                    onChange={(e) => setEditForm({ ...editForm, superficie: e.target.value })}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Nb. pièces</label>
                  <input
                    type="number"
                    value={editForm.nb_pieces}
                    onChange={(e) => setEditForm({ ...editForm, nb_pieces: e.target.value })}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
                    Description (optionnel)
                  </label>
                  <textarea
                    rows={2}
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                </div>
                <div className="flex gap-2 sm:col-span-2">
                  <button
                    type="submit"
                    disabled={savingEdit}
                    className="flex-1 rounded-md bg-[var(--color-brass)] py-2 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
                  >
                    {savingEdit ? "Enregistrement…" : "Enregistrer les modifications"}
                  </button>
                  <button
                    type="button"
                    onClick={cancelEdit}
                    className="rounded-md border border-[var(--color-line)] px-4 py-2 text-sm font-medium text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                  >
                    Annuler
                  </button>
                </div>
                <p className="text-xs text-[var(--color-ink-3)] sm:col-span-2">
                  Les photos ne sont pas modifiables ici pour le moment — supprime et
                  republie l'annonce si tu dois changer les images.
                </p>
              </form>
            ) : (
              <div className="mt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => openEdit(b)}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-md border border-[var(--color-line)] py-1.5 text-xs font-medium text-[var(--color-ink-2)] hover:border-[var(--color-brass)] hover:text-[var(--color-brass-deep)]"
                >
                  <Pencil size={13} />
                  Modifier
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(b)}
                  disabled={deletingBienId === b.id}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-md border border-[var(--color-rust)]/40 py-1.5 text-xs font-medium text-[var(--color-rust)] hover:bg-[var(--color-rust-bg)] disabled:opacity-50"
                >
                  <Trash2 size={13} />
                  {deletingBienId === b.id ? "Suppression…" : "Supprimer"}
                </button>
              </div>
            )}

            {editingLocationFor === b.id ? (
              <div className="mt-2 rounded-md border border-[var(--color-line)] bg-[var(--color-card)] p-3">
                <LocationPicker
                  latitude={editLat}
                  longitude={editLng}
                  ville={b.ville}
                  adresse={b.adresse}
                  onChange={(lat, lng) => {
                    setEditLat(lat);
                    setEditLng(lng);
                  }}
                />
                <div className="mt-2 flex gap-2">
                  <button
                    type="button"
                    onClick={() => saveLocation(b.id)}
                    disabled={savingLocation || editLat == null || editLng == null}
                    className="flex-1 rounded-md bg-[var(--color-brass)] py-1.5 text-xs font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-50"
                  >
                    {savingLocation ? "Enregistrement…" : "Enregistrer la position"}
                  </button>
                  <button
                    type="button"
                    onClick={cancelLocationEditor}
                    className="rounded-md border border-[var(--color-line)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                  >
                    Annuler
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => openLocationEditor(b)}
                className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-md border border-dashed border-[var(--color-line)] py-1.5 text-xs font-medium text-[var(--color-ink-2)] hover:border-[var(--color-brass)] hover:text-[var(--color-brass-deep)]"
              >
                {b.latitude != null && b.longitude != null
                  ? "Modifier la position sur la carte"
                  : "⚠ Non géolocalisé — cliquez pour localiser"}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
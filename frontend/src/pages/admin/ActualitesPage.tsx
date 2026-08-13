import { useEffect, useRef, useState } from "react";
import { Newspaper, ImagePlus, Trash2, Pencil, Eye, EyeOff, X, Check } from "lucide-react";
import { api, API_BASE_URL, formatErrorDetail } from "../../lib/api";
import { resolvePhotoUrl } from "../../components/ui/ImageCarousel";
import type { Actualite } from "../../types";

export default function ActualitesPage() {
  const [actualites, setActualites] = useState<Actualite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Formulaire de création
  const [titre, setTitre] = useState("");
  const [contenu, setContenu] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Édition inline d'une actualité existante
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitre, setEditTitre] = useState("");
  const [editContenu, setEditContenu] = useState("");
  const [savingId, setSavingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchAll = () => {
    setLoading(true);
    api
      .get<Actualite[]>("/actualites/admin")
      .then(setActualites)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchAll, []);

  const handleImageChange = (file: File | null) => {
    setImageFile(file);
    setImagePreview(file ? URL.createObjectURL(file) : null);
  };

  const uploadImage = async (actualiteId: string, file: File) => {
    const formData = new FormData();
    formData.append("image", file);
    const res = await fetch(`${API_BASE_URL}/actualites/${actualiteId}/image`, {
      method: "POST",
      credentials: "include", // envoie le cookie httpOnly
      body: formData,
      // Pas de Content-Type ici — le navigateur génère le boundary multipart
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(body.detail, res.status) || `Erreur upload image (${res.status})`);
    }
  };
    

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!titre.trim() || !contenu.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      const created = await api.post<Actualite>("/actualites", { titre, contenu });
      if (imageFile) {
        await uploadImage(created.id, imageFile);
      }
      setTitre("");
      setContenu("");
      handleImageChange(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de publier cette actualité");
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (a: Actualite) => {
    setEditingId(a.id);
    setEditTitre(a.titre);
    setEditContenu(a.contenu);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditTitre("");
    setEditContenu("");
  };

  const saveEdit = async (id: string) => {
    setSavingId(id);
    setError(null);
    try {
      await api.patch(`/actualites/${id}`, { titre: editTitre, contenu: editContenu });
      cancelEdit();
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d'enregistrer les modifications");
    } finally {
      setSavingId(null);
    }
  };

  const togglePublie = async (a: Actualite) => {
    setSavingId(a.id);
    setError(null);
    try {
      await api.patch(`/actualites/${a.id}`, { publie: !a.publie });
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de mettre à jour");
    } finally {
      setSavingId(null);
    }
  };

  const handleDelete = async (a: Actualite) => {
    const confirmed = window.confirm(`Supprimer définitivement l'actualité « ${a.titre} » ?`);
    if (!confirmed) return;

    setDeletingId(a.id);
    setError(null);
    try {
      await api.del(`/actualites/${a.id}`);
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de supprimer cette actualité");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Actualités</h1>
      <p className="mt-1 text-sm text-[var(--color-ink-3)]">
        Publiez des actualités affichées sur la page d'accueil publique. Une actualité
        dépubliée reste ici mais disparaît de la page d'accueil.
      </p>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}

      {/* Formulaire de création */}
      <form
        onSubmit={handleCreate}
        className="mt-6 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-5"
      >
        <h2 className="flex items-center gap-2 font-display text-base text-[var(--color-ink)]">
          <Newspaper size={16} />
          Nouvelle actualité
        </h2>

        <div className="mt-4">
          <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Titre</label>
          <input
            required
            value={titre}
            onChange={(e) => setTitre(e.target.value)}
            placeholder="Ex. : Nouvelle fonctionnalité de recherche avancée"
            className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)]"
          />
        </div>

        <div className="mt-3">
          <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Contenu</label>
          <textarea
            required
            rows={4}
            value={contenu}
            onChange={(e) => setContenu(e.target.value)}
            placeholder="Détail de l'actualité…"
            className="w-full resize-none rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)]"
          />
        </div>

        <div className="mt-3">
          <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
            Image (optionnelle)
          </label>
          <div className="flex items-center gap-3">
            <label className="flex cursor-pointer items-center gap-1.5 rounded-md border border-[var(--color-line)] px-3 py-2 text-xs font-medium text-[var(--color-ink-2)] hover:border-[var(--color-brass)] hover:text-[var(--color-brass-deep)]">
              <ImagePlus size={14} />
              Choisir une image
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => handleImageChange(e.target.files?.[0] ?? null)}
              />
            </label>
            {imagePreview && (
              <img src={imagePreview} alt="Aperçu" className="h-12 w-12 rounded-md object-cover" />
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="mt-4 rounded-md bg-[var(--color-brass)] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
        >
          {submitting ? "Publication…" : "Publier l'actualité"}
        </button>
      </form>

      {/* Liste des actualités existantes */}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && actualites.length === 0 && !error && (
        <p className="mt-8 flex items-center gap-2 text-sm text-[var(--color-ink-3)]">
          <Newspaper size={16} />
          Aucune actualité publiée pour le moment.
        </p>
      )}

      <div className="mt-8 space-y-3">
        {actualites.map((a) => {
          const isEditing = editingId === a.id;
          return (
            <div key={a.id} className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4">
              {isEditing ? (
                <div className="space-y-2">
                  <input
                    value={editTitre}
                    onChange={(e) => setEditTitre(e.target.value)}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)]"
                  />
                  <textarea
                    rows={3}
                    value={editContenu}
                    onChange={(e) => setEditContenu(e.target.value)}
                    className="w-full resize-none rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)]"
                  />
                  <div className="flex gap-2">
                    <button
                      disabled={savingId === a.id}
                      onClick={() => saveEdit(a.id)}
                      className="flex items-center gap-1.5 rounded-md bg-[var(--color-brass)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
                    >
                      <Check size={13} />
                      {savingId === a.id ? "Enregistrement…" : "Enregistrer"}
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-2)]"
                    >
                      <X size={13} />
                      Annuler
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex gap-4">
                  {a.image_url && (
                    <img
                      src={resolvePhotoUrl(a.image_url)}
                      alt={a.titre}
                      className="h-20 w-20 shrink-0 rounded-md object-cover"
                    />
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-medium text-[var(--color-ink)]">{a.titre}</p>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          a.publie
                            ? "bg-[var(--color-sage-bg)] text-[var(--color-sage)]"
                            : "bg-[var(--color-paper-2)] text-[var(--color-ink-3)]"
                        }`}
                      >
                        {a.publie ? "Publiée" : "Dépubliée"}
                      </span>
                    </div>
                    <p className="mt-1 whitespace-pre-wrap text-sm text-[var(--color-ink-2)]">{a.contenu}</p>
                    <p className="mt-2 font-mono text-xs text-[var(--color-ink-3)]">
                      {new Date(a.date_creation).toLocaleDateString("fr-MA")}
                      {a.auteur_prenom && ` — par ${a.auteur_prenom} ${a.auteur_nom ?? ""}`}
                    </p>

                    <div className="mt-3 flex flex-wrap gap-2">
                      <button
                        disabled={savingId === a.id}
                        onClick={() => togglePublie(a)}
                        className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-2)] hover:border-[var(--color-brass)] hover:text-[var(--color-brass-deep)] disabled:opacity-60"
                      >
                        {a.publie ? <EyeOff size={13} /> : <Eye size={13} />}
                        {a.publie ? "Dépublier" : "Republier"}
                      </button>
                      <button
                        onClick={() => startEdit(a)}
                        className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-2)] hover:border-[var(--color-brass)] hover:text-[var(--color-brass-deep)]"
                      >
                        <Pencil size={13} />
                        Modifier
                      </button>
                      <button
                        disabled={deletingId === a.id}
                        onClick={() => handleDelete(a)}
                        className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-2)] hover:border-[var(--color-rust)] hover:text-[var(--color-rust)] disabled:opacity-60"
                      >
                        <Trash2 size={13} />
                        {deletingId === a.id ? "Suppression…" : "Supprimer"}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

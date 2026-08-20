import { useEffect, useRef, useState } from "react";
import { Newspaper, ImagePlus, Trash2, Pencil, Eye, EyeOff, X, Check } from "lucide-react";
import { api, API_BASE_URL, formatErrorDetail } from "../../lib/api";
import { resolvePhotoUrl } from "../ui/ImageCarousel";
import { useAuth } from "../../lib/auth";
import RichTextEditor from "./RichTextEditor";
import {
  CATEGORIES_ARTICLE,
  LABEL_CATEGORIE,
  type Actualite,
  type CategorieArticle,
} from "../../types";

/**
 * Gestion des articles de blog — composant partagé entre l'espace admin
 * (`pages/admin/ActualitesPage.tsx`) et l'espace agence
 * (`pages/agence/BlogPage.tsx`), pour garantir un comportement identique.
 *
 * Le filtrage "un admin voit tout, une agence ne voit que ses propres
 * articles" est déjà géré côté back (`GET /actualites/admin`) — ce
 * composant affiche simplement ce que l'API renvoie, sans logique de rôle
 * dupliquée côté front pour la visibilité. Seul le petit badge "auteur"
 * (visible uniquement pour un admin, utile en modération) dépend du rôle
 * courant.
 */
export default function BlogManager() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [articles, setArticles] = useState<Actualite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Formulaire de création
  const [titre, setTitre] = useState("");
  const [extrait, setExtrait] = useState("");
  const [categorie, setCategorie] = useState<CategorieArticle>("actualite");
  const [contenuHtml, setContenuHtml] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formOuvert, setFormOuvert] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Édition inline d'un article existant
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitre, setEditTitre] = useState("");
  const [editExtrait, setEditExtrait] = useState("");
  const [editCategorie, setEditCategorie] = useState<CategorieArticle>("actualite");
  const [editContenuHtml, setEditContenuHtml] = useState("");
  const [savingId, setSavingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchAll = () => {
    setLoading(true);
    api
      .get<Actualite[]>("/actualites/admin")
      .then(setArticles)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchAll, []);

  const resetForm = () => {
    setTitre("");
    setExtrait("");
    setCategorie("actualite");
    setContenuHtml("");
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    setFormOuvert(false);
  };

  const handleImageChange = (file: File | null) => {
    setImageFile(file);
    setImagePreview(file ? URL.createObjectURL(file) : null);
  };

  const uploadCouverture = async (articleId: string, file: File) => {
    const formData = new FormData();
    formData.append("image", file);
    const res = await fetch(`${API_BASE_URL}/actualites/${articleId}/image`, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(formatErrorDetail(body.detail, res.status) || `Erreur upload image (${res.status})`);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    const contenuVide = contenuHtml.replace(/<[^>]*>/g, "").trim().length === 0;
    if (!titre.trim() || contenuVide) {
      setError("Le titre et le contenu de l'article sont obligatoires.");
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const created = await api.post<Actualite>("/actualites", {
        titre,
        contenu_html: contenuHtml,
        extrait: extrait.trim() || undefined,
        categorie,
      });
      if (imageFile) {
        await uploadCouverture(created.id, imageFile);
      }
      resetForm();
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de publier cet article");
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (a: Actualite) => {
    setEditingId(a.id);
    setEditTitre(a.titre);
    setEditExtrait(a.extrait ?? "");
    setEditCategorie(a.categorie);
    setEditContenuHtml(a.contenu_html);
  };

  const cancelEdit = () => setEditingId(null);

  const saveEdit = async (id: string) => {
    setSavingId(id);
    setError(null);
    try {
      await api.patch(`/actualites/${id}`, {
        titre: editTitre,
        contenu_html: editContenuHtml,
        extrait: editExtrait.trim() || undefined,
        categorie: editCategorie,
      });
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
    const confirmed = window.confirm(`Supprimer définitivement l'article « ${a.titre} » ?`);
    if (!confirmed) return;

    setDeletingId(a.id);
    setError(null);
    try {
      await api.del(`/actualites/${a.id}`);
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de supprimer cet article");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Blog</h1>
          <p className="mt-1 text-sm text-[var(--color-ink-3)]">
            {isAdmin
              ? "Rédigez des articles ou modérez ceux publiés par les agences. Un article dépublié reste ici mais disparaît du blog public."
              : "Rédigez des articles publiés sous le nom de votre agence sur le blog ImmoVision. Un article dépublié reste ici mais disparaît du blog public."}
          </p>
        </div>
        {!formOuvert && (
          <button
            type="button"
            onClick={() => setFormOuvert(true)}
            className="flex items-center gap-1.5 rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)]"
          >
            <Newspaper size={15} />
            Nouvel article
          </button>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}

      {/* Formulaire de création */}
      {formOuvert && (
        <form
          onSubmit={handleCreate}
          className="mt-6 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-5"
        >
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-display text-base text-[var(--color-ink)]">
              <Newspaper size={16} />
              Nouvel article
            </h2>
            <button
              type="button"
              onClick={resetForm}
              className="text-[var(--color-ink-3)] hover:text-[var(--color-ink)]"
              aria-label="Fermer"
            >
              <X size={16} />
            </button>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-[2fr_1fr]">
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Titre</label>
              <input
                required
                value={titre}
                onChange={(e) => setTitre(e.target.value)}
                placeholder="Ex. : Comment estimer le loyer d'un appartement à Casablanca"
                className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)]"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Catégorie</label>
              <select
                value={categorie}
                onChange={(e) => setCategorie(e.target.value as CategorieArticle)}
                className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)]"
              >
                {CATEGORIES_ARTICLE.map((c) => (
                  <option key={c} value={c}>
                    {LABEL_CATEGORIE[c]}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-3">
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
              Extrait (résumé affiché sur les cartes — optionnel, généré depuis le contenu sinon)
            </label>
            <input
              value={extrait}
              onChange={(e) => setExtrait(e.target.value.slice(0, 300))}
              placeholder="Résumé en une phrase…"
              maxLength={300}
              className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)]"
            />
          </div>

          <div className="mt-3">
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Contenu</label>
            <RichTextEditor content={contenuHtml} onChange={setContenuHtml} />
          </div>

          <div className="mt-3">
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
              Image de couverture (optionnelle)
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
            {submitting ? "Publication…" : "Publier l'article"}
          </button>
        </form>
      )}

      {/* Liste des articles existants */}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && articles.length === 0 && !error && (
        <p className="mt-8 flex items-center gap-2 text-sm text-[var(--color-ink-3)]">
          <Newspaper size={16} />
          Aucun article pour le moment.
        </p>
      )}

      <div className="mt-8 space-y-3">
        {articles.map((a) => {
          const isEditing = editingId === a.id;
          const peutModifier = isAdmin || a.auteur_role !== "admin";
          return (
            <div key={a.id} className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4">
              {isEditing ? (
                <div className="space-y-2">
                  <input
                    value={editTitre}
                    onChange={(e) => setEditTitre(e.target.value)}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)]"
                  />
                  <select
                    value={editCategorie}
                    onChange={(e) => setEditCategorie(e.target.value as CategorieArticle)}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)]"
                  >
                    {CATEGORIES_ARTICLE.map((c) => (
                      <option key={c} value={c}>
                        {LABEL_CATEGORIE[c]}
                      </option>
                    ))}
                  </select>
                  <input
                    value={editExtrait}
                    onChange={(e) => setEditExtrait(e.target.value.slice(0, 300))}
                    placeholder="Extrait…"
                    maxLength={300}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)]"
                  />
                  <RichTextEditor content={editContenuHtml} onChange={setEditContenuHtml} />
                  <div className="flex gap-2 pt-1">
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
                      <div className="flex items-center gap-2">
                        <span className="rounded-full bg-[var(--color-paper-2)] px-2 py-0.5 text-xs text-[var(--color-ink-3)]">
                          {LABEL_CATEGORIE[a.categorie]}
                        </span>
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                            a.publie
                              ? "bg-[var(--color-sage-bg)] text-[var(--color-sage)]"
                              : "bg-[var(--color-paper-2)] text-[var(--color-ink-3)]"
                          }`}
                        >
                          {a.publie ? "Publié" : "Dépublié"}
                        </span>
                      </div>
                    </div>
                    {a.extrait && (
                      <p className="mt-1 text-sm text-[var(--color-ink-2)]">{a.extrait}</p>
                    )}
                    <p className="mt-2 font-mono text-xs text-[var(--color-ink-3)]">
                      {new Date(a.date_creation).toLocaleDateString("fr-MA")}
                      {" — par "}
                      {a.auteur_affichage}
                      {isAdmin && a.auteur_prenom && ` (${a.auteur_prenom} ${a.auteur_nom ?? ""})`}
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
                      {peutModifier && (
                        <>
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
                        </>
                      )}
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

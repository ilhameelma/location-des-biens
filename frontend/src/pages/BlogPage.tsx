import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, CalendarDays, Newspaper } from "lucide-react";
import { api } from "../lib/api";
import { CATEGORIES_ARTICLE, LABEL_CATEGORIE, type Actualite, type CategorieArticle } from "../types";
import { resolvePhotoUrl } from "../components/ui/ImageCarousel";
import { stripHtml } from "../lib/htmlUtils";
import SiteFooter from "../components/layout/SiteFooter";
import PublierAnnonceButton from "../components/publish/PublierAnnonceButton";
import logo from "../assets/logo_immo1.png";

/**
 * Page publique listant l'intégralité des articles de blog publiés —
 * accessible à tout visiteur, connecté ou non, depuis le lien "Voir tous
 * les articles" de la landing page. Chaque carte renvoie vers la fiche
 * article dédiée (/blog/:slug), pas de contenu complet ici.
 */
export default function BlogPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const categorieActive = searchParams.get("categorie") as CategorieArticle | null;

  const [articles, setArticles] = useState<Actualite[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    const params = new URLSearchParams();
    if (categorieActive) params.set("categorie", categorieActive);
    api
      .get<Actualite[]>(`/actualites?${params.toString()}`)
      .then((data) => {
        if (active) setArticles(data);
      })
      .catch(() => {
        if (active) setArticles([]);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [categorieActive]);

  const setCategorie = (c: CategorieArticle | null) => {
    if (c) setSearchParams({ categorie: c });
    else setSearchParams({});
  };

  return (
    <div className="min-h-screen bg-[var(--color-paper)]">
      <header className="sticky top-0 z-40 border-b border-[var(--color-line)] bg-[var(--color-paper)]/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
          <Link to="/" className="flex items-center gap-2.5">
            <img src={logo} alt="ImmoVision" className="h-11 w-auto" />
            <span className="font-display text-xl font-semibold text-[var(--color-ink)]">
              ImmoVision
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <PublierAnnonceButton variant="outline" className="hidden sm:inline-flex" />
            <PublierAnnonceButton variant="icon" className="sm:hidden" />
            <button
              type="button"
              onClick={() => navigate("/")}
              className="flex items-center gap-1.5 text-sm font-medium text-[var(--color-ink-2)] hover:text-[var(--color-brass-deep)]"
            >
              <ArrowLeft size={15} />
              Retour à l'accueil
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-16">
        <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
          Blog
        </span>
        <h1 className="mt-4 font-display text-3xl text-[var(--color-ink)]">
          Le blog ImmoVision
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[var(--color-ink-2)]">
          Conseils, guides pratiques et actualités sur le marché immobilier marocain — rédigés
          par notre équipe et par les agences partenaires de la plateforme.
        </p>

        <div className="mt-8 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setCategorie(null)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
              !categorieActive
                ? "border-[var(--color-brass)] bg-[var(--color-brass)] text-white"
                : "border-[var(--color-line)] text-[var(--color-ink-2)] hover:border-[var(--color-brass)]"
            }`}
          >
            Tous les articles
          </button>
          {CATEGORIES_ARTICLE.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setCategorie(c)}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                categorieActive === c
                  ? "border-[var(--color-brass)] bg-[var(--color-brass)] text-white"
                  : "border-[var(--color-line)] text-[var(--color-ink-2)] hover:border-[var(--color-brass)]"
              }`}
            >
              {LABEL_CATEGORIE[c]}
            </button>
          ))}
        </div>

        {loading && (
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-64 animate-pulse rounded-lg bg-[var(--color-paper-2)]" />
            ))}
          </div>
        )}

        {!loading && articles.length === 0 && (
          <p className="mt-10 flex items-center gap-2 text-sm text-[var(--color-ink-3)]">
            <Newspaper size={16} />
            Aucun article publié pour le moment{categorieActive ? " dans cette catégorie" : ""}.
          </p>
        )}

        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {articles.map((a) => (
            <article
              key={a.id}
              className="overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)]"
            >
              <Link to={`/blog/${a.slug}`} className="block">
                <div className="relative h-40 w-full overflow-hidden bg-[var(--color-paper-2)]">
                  {a.image_url ? (
                    <img
                      src={resolvePhotoUrl(a.image_url)}
                      alt={a.titre}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-[var(--color-ink-3)]">
                      <Newspaper size={26} />
                    </div>
                  )}
                </div>
              </Link>
              <div className="space-y-2 p-5">
                <div className="flex items-center justify-between gap-2">
                  <p className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide text-[var(--color-brass-deep)]">
                    <CalendarDays size={12} />
                    {new Date(a.date_creation).toLocaleDateString("fr-FR", {
                      day: "numeric",
                      month: "long",
                      year: "numeric",
                    })}
                  </p>
                  <span className="rounded-full bg-[var(--color-paper-2)] px-2 py-0.5 text-[10px] text-[var(--color-ink-3)]">
                    {LABEL_CATEGORIE[a.categorie]}
                  </span>
                </div>
                <Link to={`/blog/${a.slug}`}>
                  <h2 className="font-display text-base leading-snug text-[var(--color-ink)] hover:text-[var(--color-brass-deep)]">
                    {a.titre}
                  </h2>
                </Link>
                <p className="line-clamp-3 text-sm leading-relaxed text-[var(--color-ink-2)]">
                  {a.extrait || stripHtml(a.contenu_html)}
                </p>
                <p className="text-xs text-[var(--color-ink-3)]">Par {a.auteur_affichage}</p>
                <Link
                  to={`/blog/${a.slug}`}
                  className="inline-flex items-center gap-1 pt-1 text-sm font-medium text-[var(--color-brass-deep)] hover:underline"
                >
                  Lire la suite
                  <ArrowRight size={13} />
                </Link>
              </div>
            </article>
          ))}
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}

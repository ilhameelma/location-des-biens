import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, CalendarDays } from "lucide-react";
import { api } from "../lib/api";
import type { Actualite } from "../types";
import { LABEL_CATEGORIE } from "../types";
import { resolvePhotoUrl } from "../components/ui/ImageCarousel";
import { stripHtml } from "../lib/htmlUtils";
import SiteFooter from "../components/layout/SiteFooter";
import PublierAnnonceButton from "../components/publish/PublierAnnonceButton";
import logo from "../assets/logo_immo1.png";

/**
 * Fiche article publique (/blog/:slug) — contenu complet, rendu depuis le
 * HTML déjà sanitizé côté serveur (nh3, voir routers/actualites.py) avant
 * stockage. dangerouslySetInnerHTML est acceptable ici précisément parce
 * que la sanitization a déjà eu lieu en amont, pas parce qu'on lui fait
 * confiance par défaut.
 *
 * Titre de l'onglet + meta description mis à jour dynamiquement pour le
 * référencement (chaque article a une URL et des métadonnées propres,
 * contrairement à l'ancien `/actualites#id`).
 */
export default function BlogArticlePage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [article, setArticle] = useState<Actualite | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!slug) return;
    let active = true;
    setLoading(true);
    setNotFound(false);
    api
      .get<Actualite>(`/actualites/slug/${slug}`)
      .then((data) => {
        if (active) setArticle(data);
      })
      .catch(() => {
        if (active) setNotFound(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [slug]);

  useEffect(() => {
    if (!article) return;
    const previousTitle = document.title;
    document.title = `${article.titre} — Blog ImmoVision`;

    const description = article.extrait || stripHtml(article.contenu_html, 160);
    const metaTag = document.querySelector('meta[name="description"]');
    const previousDescription = metaTag?.getAttribute("content") ?? null;
    if (metaTag) metaTag.setAttribute("content", description);

    return () => {
      document.title = previousTitle;
      if (metaTag && previousDescription !== null) metaTag.setAttribute("content", previousDescription);
    };
  }, [article]);

  return (
    <div className="min-h-screen bg-[var(--color-paper)]">
      <header className="sticky top-0 z-40 border-b border-[var(--color-line)] bg-[var(--color-paper)]/95 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-3">
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
              onClick={() => navigate("/blog")}
              className="flex items-center gap-1.5 text-sm font-medium text-[var(--color-ink-2)] hover:text-[var(--color-brass-deep)]"
            >
              <ArrowLeft size={15} />
              Retour au blog
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-16">
        {loading && (
          <div className="space-y-4">
            <div className="h-56 animate-pulse rounded-lg bg-[var(--color-paper-2)]" />
            <div className="h-8 w-2/3 animate-pulse rounded bg-[var(--color-paper-2)]" />
            <div className="h-4 w-full animate-pulse rounded bg-[var(--color-paper-2)]" />
          </div>
        )}

        {!loading && notFound && (
          <div className="py-16 text-center">
            <p className="font-display text-xl text-[var(--color-ink)]">Article introuvable</p>
            <p className="mt-2 text-sm text-[var(--color-ink-3)]">
              Cet article n'existe pas ou n'est plus publié.
            </p>
            <Link
              to="/blog"
              className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-[var(--color-brass-deep)] hover:underline"
            >
              <ArrowLeft size={14} />
              Retour au blog
            </Link>
          </div>
        )}

        {!loading && article && (
          <article>
            {article.image_url && (
              <div className="mb-6 h-64 w-full overflow-hidden rounded-lg bg-[var(--color-paper-2)]">
                <img
                  src={resolvePhotoUrl(article.image_url)}
                  alt={article.titre}
                  className="h-full w-full object-cover"
                />
              </div>
            )}

            <span className="rounded-full bg-[var(--color-paper-2)] px-2.5 py-1 text-xs font-medium text-[var(--color-brass-deep)]">
              {LABEL_CATEGORIE[article.categorie]}
            </span>

            <h1 className="mt-3 font-display text-3xl leading-tight text-[var(--color-ink)]">
              {article.titre}
            </h1>

            <div className="mt-3 flex items-center gap-4 text-xs text-[var(--color-ink-3)]">
              <p className="flex items-center gap-1.5">
                <CalendarDays size={13} />
                {new Date(article.date_creation).toLocaleDateString("fr-FR", {
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                })}
              </p>
              <p>Par {article.auteur_affichage}</p>
            </div>

            <div
              className="prose-article mt-8 max-w-none text-[15px] leading-relaxed text-[var(--color-ink-2)] [&_a]:text-[var(--color-brass-deep)] [&_a]:underline [&_blockquote]:border-l-2 [&_blockquote]:border-[var(--color-brass)] [&_blockquote]:pl-4 [&_blockquote]:italic [&_h2]:mt-8 [&_h2]:font-display [&_h2]:text-2xl [&_h2]:text-[var(--color-ink)] [&_h3]:mt-6 [&_h3]:font-display [&_h3]:text-xl [&_h3]:text-[var(--color-ink)] [&_h4]:mt-4 [&_h4]:font-display [&_h4]:text-lg [&_h4]:text-[var(--color-ink)] [&_img]:my-4 [&_img]:rounded-lg [&_li]:my-1 [&_ol]:my-3 [&_ol]:list-decimal [&_ol]:pl-6 [&_p]:my-3 [&_ul]:my-3 [&_ul]:list-disc [&_ul]:pl-6"
              // Contenu déjà sanitizé côté serveur (nh3) avant écriture en
              // base — voir le commentaire de composant ci-dessus.
              dangerouslySetInnerHTML={{ __html: article.contenu_html }}
            />
          </article>
        )}
      </main>

      <SiteFooter />
    </div>
  );
}

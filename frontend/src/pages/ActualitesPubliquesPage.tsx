import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, CalendarDays, Newspaper } from "lucide-react";
import { api } from "../lib/api";
import type { Actualite } from "../types";
import { resolvePhotoUrl } from "../components/ui/ImageCarousel";
import SiteFooter from "../components/layout/SiteFooter";
import PublierAnnonceButton from "../components/publish/PublierAnnonceButton";
import logo from "../assets/logo_immo1.png";

/**
 * Page publique listant l'intégralité des actualités publiées (contenu
 * complet, pas de troncature) — accessible à tout visiteur, connecté ou
 * non, depuis le lien "Voir toutes les actualités" de la landing page.
 */
export default function ActualitesPubliquesPage() {
  const navigate = useNavigate();
  const [actualites, setActualites] = useState<Actualite[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    api
      .get<Actualite[]>("/actualites")
      .then((data) => {
        if (active) setActualites(data);
      })
      .catch(() => {
        if (active) setActualites([]);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

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
              onClick={() => navigate("/")}
              className="flex items-center gap-1.5 text-sm font-medium text-[var(--color-ink-2)] hover:text-[var(--color-brass-deep)]"
            >
              <ArrowLeft size={15} />
              Retour à l'accueil
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-16">
        <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
          Actualités
        </span>
        <h1 className="mt-4 font-display text-3xl text-[var(--color-ink)]">
          Toutes les actualités d'ImmoVision
        </h1>

        {loading && (
          <div className="mt-10 space-y-8">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-40 animate-pulse rounded-lg bg-[var(--color-paper-2)]" />
            ))}
          </div>
        )}

        {!loading && actualites.length === 0 && (
          <p className="mt-10 flex items-center gap-2 text-sm text-[var(--color-ink-3)]">
            <Newspaper size={16} />
            Aucune actualité publiée pour le moment.
          </p>
        )}

        <div className="mt-10 space-y-10">
          {actualites.map((a) => (
            <article key={a.id} id={a.id} className="scroll-mt-24 border-b border-[var(--color-line)] pb-10 last:border-b-0">
              {a.image_url && (
                <div className="mb-4 h-56 w-full overflow-hidden rounded-lg bg-[var(--color-paper-2)]">
                  <img
                    src={resolvePhotoUrl(a.image_url)}
                    alt={a.titre}
                    className="h-full w-full object-cover"
                  />
                </div>
              )}
              <p className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide text-[var(--color-brass-deep)]">
                <CalendarDays size={12} />
                {new Date(a.date_creation).toLocaleDateString("fr-FR", {
                  day: "numeric",
                  month: "long",
                  year: "numeric",
                })}
              </p>
              <h2 className="mt-2 font-display text-2xl text-[var(--color-ink)]">{a.titre}</h2>
              <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-[var(--color-ink-2)]">
                {a.contenu}
              </p>
            </article>
          ))}
        </div>
      </main>

      <SiteFooter />
    </div>
  );
}

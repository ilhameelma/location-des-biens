import { useEffect, useState, type CSSProperties, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  Search,
  FileSignature,
  Wallet,
  MessageSquare,
  BarChart3,
  ShieldAlert,
  MapPin,
  Sparkles,
  Building2,
  Key,
  Mail,
  Phone,
  Send,
  ArrowRight,
  CheckCircle2,
  Lock,
  ImageIcon,
  Landmark,
  BadgeDollarSign,
  Handshake,
  UserCog,
  Newspaper,
  CalendarDays,
  MessageCircle,
  Loader2,
} from "lucide-react";
import { api } from "../lib/api";
import type { Actualite, Bien } from "../types";
import { stripHtml } from "../lib/htmlUtils";

/** Métriques publiques calculées côté back-end (GET /stats/publiques). */
interface StatsPubliques {
  biens_en_ligne: number;
  villes_couvertes: number;
  espaces_dedies: number;
}
import { resolvePhotoUrl } from "../components/ui/ImageCarousel";
import { CONTACT_EMAIL } from "../components/layout/SiteFooter";
import SiteHeader from "../components/layout/SiteHeader";
import SiteFooter from "../components/layout/SiteFooter";
import PublierAnnonceButton from "../components/publish/PublierAnnonceButton";
import hero from "../assets/home6.png";

// Numéro WhatsApp de contact (format international, sans espaces ni "+",
// tel qu'exigé par l'URL wa.me) — à adapter avec le vrai numéro de la
// plateforme. Le "+212 5 00 00 00 00" affiché ailleurs sur la page est un
// numéro fixe indicatif ; WhatsApp nécessite un numéro mobile réel.
const WHATSAPP_NUMBER = "212637808129";

// Arc en fer à cheval (référence à l'architecture marocaine) utilisé comme
// signature visuelle pour les images de la page — rayon horizontal large,
// rayon vertical réduit, exprimés en % pour rester proportionnels au conteneur.
const ARCH_STYLE: CSSProperties = {
  borderRadius: "50% 50% 0 0 / 18% 18% 0 0",
};

const SERVICES = [
  {
    icon: Search,
    title: "Recherche multicritères",
    text: "Filtrez par ville, type de bien, prix et superficie pour trouver l'annonce qui correspond exactement à votre besoin.",
  },
  {
    icon: FileSignature,
    title: "Réservation & contrats",
    text: "Réservez en un clic : le contrat de location est généré automatiquement dès la confirmation du propriétaire.",
  },
  {
    icon: Wallet,
    title: "Paiements suivis",
    text: "Chaque paiement est enregistré et rattaché à son contrat, consultable à tout moment par le locataire et le propriétaire.",
  },
  {
    icon: MessageSquare,
    title: "Messagerie instantanée",
    text: "Échangez en temps réel avec un propriétaire ou un locataire, directement depuis la fiche de l'annonce.",
  },
  {
    icon: Sparkles,
    title: "Estimation de loyer par IA",
    text: "Un modèle entraîné sur le marché marocain suggère une fourchette de prix réaliste au moment de la publication.",
  },
  {
    icon: MapPin,
    title: "Carte interactive",
    text: "Visualisez les biens disponibles sur une carte et affinez votre recherche par quartier.",
  },
  {
    icon: ShieldAlert,
    title: "Détection de fraude",
    text: "Chaque annonce est passée au crible d'un modèle de détection d'anomalies avant validation par l'administration.",
  },
  {
    icon: BarChart3,
    title: "Tableaux de bord",
    text: "Propriétaires et administrateurs suivent revenus, taux d'occupation et activité via des indicateurs actualisés.",
  },
];

const ACTORS = [
  {
    icon: Key,
    role: "Client",
    text: "Recherche un bien immobilier, applique des filtres, réserve, signe son contrat, effectue ses paiements et échange avec les propriétaires.",
  },
  {
    icon: Building2,
    role: "Propriétaire",
    text: "Publie ses biens (maison, appartement, magasin, garage...), gère ses annonces, reçoit les demandes et suit ses revenus.",
  },
  {
    icon: Landmark,
    role: "Agence immobilière",
    text: "Gère un portefeuille de biens, accompagne les clients dans leurs recherches et assure la mise en relation entre propriétaires et locataires.",
  },
  {
    icon: BadgeDollarSign,
    role: "Promoteur immobilier",
    text: "Présente ses projets immobiliers neufs, commercialise ses biens et suit les demandes des acheteurs ou locataires.",
  },
  {
    icon: Handshake,
    role: "Courtier (Samsar)",
    text: "Facilite les transactions immobilières, met en relation les parties et accompagne les clients dans leurs démarches.",
  },
  {
    icon: UserCog,
    role: "Administrateur",
    text: "Contrôle les utilisateurs, valide les comptes professionnels, supervise les annonces et garantit la sécurité de la plateforme.",
  },
];

const TYPE_LABELS: Record<string, string> = {
  maison: "Maison",
  appartement: "Appartement",
  magasin: "Magasin",
  garage: "Garage",
  bureau: "Bureau",
  terrain: "Terrain",
  villa: "Villa",
};

// Carte "aperçu" utilisée uniquement sur la landing page : montre une vraie
// annonce (image, ville, prix) à titre d'exemple, mais ne mène JAMAIS vers la
// fiche détaillée (/biens/:id, route protégée) — un visiteur non connecté ne
// doit pas se retrouver redirigé silencieusement. Le badge "Connexion
// requise" est visible en permanence (pas seulement au survol, pour rester
// clair sur mobile où il n'y a pas de hover).
function ListingPreviewCard({ bien }: { bien: Bien }) {
  const photo = [...bien.photos].sort((a, b) => a.ordre - b.ordre)[0];
  const isVente = bien.type_transaction === "vente";

  return (
    <Link
      to="/login"
      className="group relative block overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] transition-shadow hover:shadow-md"
    >
      <span className="absolute right-3 top-3 z-10 inline-flex items-center gap-1 rounded-full bg-[var(--color-ink)]/85 px-2.5 py-1 text-[11px] font-medium text-white">
        <Lock size={11} />
        Connexion requise
      </span>
      <span className="absolute left-3 top-3 z-10 inline-flex items-center rounded-full bg-white/90 px-2.5 py-1 font-mono text-xs font-medium uppercase tracking-wide text-[var(--color-ink-2)]">
        {isVente ? "À vendre" : "À louer"}
      </span>

      <div className="relative h-48 w-full overflow-hidden bg-[var(--color-paper-2)]">
        {photo ? (
          <img
            src={resolvePhotoUrl(photo.url)}
            alt={bien.titre}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-[var(--color-ink-3)]">
            <ImageIcon size={28} />
          </div>
        )}

        {/* Voile au survol (desktop) — renforce le message du badge permanent */}
        <div className="absolute inset-0 flex items-center justify-center bg-[var(--color-ink)]/0 opacity-0 transition-all duration-200 group-hover:bg-[var(--color-ink)]/60 group-hover:opacity-100">
          <span className="flex items-center gap-1.5 text-sm font-medium text-white opacity-0 transition-opacity duration-200 group-hover:opacity-100">
            <Lock size={14} />
            Se connecter pour voir cette annonce
          </span>
        </div>
      </div>

      <div className="space-y-1.5 p-4">
        <span className="font-mono text-[11px] uppercase tracking-wide text-[var(--color-brass-deep)]">
          {TYPE_LABELS[bien.type_bien] ?? bien.type_bien}
        </span>
        <h3 className="font-display text-base leading-snug text-[var(--color-ink)]">{bien.titre}</h3>
        <div className="flex items-center gap-1.5 text-sm text-[var(--color-ink-2)]">
          <MapPin size={13} />
          {bien.ville}
        </div>
        <div className="flex items-baseline gap-1 pt-1">
          <span className="font-mono text-base font-semibold text-[var(--color-ink)]">
            {bien.prix.toLocaleString("fr-MA")} MAD
          </span>
          {!isVente && <span className="text-xs text-[var(--color-ink-3)]">/ mois</span>}
        </div>
      </div>
    </Link>
  );
}

export default function LandingPage() {
  const [biens, setBiens] = useState<Bien[]>([]);
  const [loadingBiens, setLoadingBiens] = useState(true);

  // Étape "métriques dynamiques" : biens en ligne / villes couvertes /
  // espaces dédiés calculés en base par le back-end (endpoint dédié,
  // `GET /stats/publiques`) plutôt que déduits de la liste de biens
  // affichée sur la page (qui peut être plafonnée par la recherche).
  const [stats, setStats] = useState<StatsPubliques | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);

  const [actualites, setActualites] = useState<Actualite[]>([]);
  const [loadingActualites, setLoadingActualites] = useState(true);

  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactMessage, setContactMessage] = useState("");
  const [contactSending, setContactSending] = useState(false);
  const [contactSent, setContactSent] = useState(false);
  const [contactError, setContactError] = useState<string | null>(null);

  // Défilement vers la section correspondante quand on arrive avec un hash
  // dans l'URL (ex. "/#services") — nécessaire car SiteHeader.tsx (utilisé
  // aussi depuis d'autres pages comme /publier) construit ses liens d'ancre
  // en "/#..." plutôt qu'en simple "#..." : une navigation React Router
  // vers une autre page ne déclenche pas de défilement automatique du
  // navigateur, contrairement à un vrai changement de page classique.
  useEffect(() => {
    if (!window.location.hash) return;
    const id = window.location.hash.slice(1);
    const scrollToHash = () => {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    // Léger délai pour laisser le temps aux images/sections de se mettre en
    // page avant de calculer la position de défilement.
    const timer = setTimeout(scrollToHash, 100);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    let active = true;
    api
      .get<Bien[]>("/biens")
      .then((data) => {
        if (active) setBiens(data);
      })
      .catch(() => {
        if (active) setBiens([]);
      })
      .finally(() => {
        if (active) setLoadingBiens(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    api
      .get<StatsPubliques>("/stats/publiques")
      .then((data) => {
        if (active) setStats(data);
      })
      .catch(() => {
        if (active) setStats(null);
      })
      .finally(() => {
        if (active) setLoadingStats(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    api
      .get<Actualite[]>("/actualites?limite=3")
      .then((data) => {
        if (active) setActualites(data);
      })
      .catch(() => {
        if (active) setActualites([]);
      })
      .finally(() => {
        if (active) setLoadingActualites(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const handleContactSubmit = (e: FormEvent) => {
    e.preventDefault();
    setContactError(null);
    setContactSending(true);
    api
      .post<void>(
        "/contact",
        { nom: contactName, email: contactEmail, message: contactMessage },
        { auth: false },
      )
      .then(() => {
        setContactSent(true);
        setContactName("");
        setContactEmail("");
        setContactMessage("");
      })
      .catch((err: Error) => {
        setContactError(err.message || "Une erreur est survenue. Merci de réessayer.");
      })
      .finally(() => setContactSending(false));
  };

  return (
    <div className="min-h-screen bg-[var(--color-paper)]">
      {/* ================= NAVIGATION ================= */}
      <SiteHeader />

      {/* ================= HERO ================= */}
      <section id="top" className="mx-auto max-w-7xl px-4 pb-20 pt-16 md:pt-24">
        <div className="grid items-center gap-1 md:grid-cols-2">
          <div>
            <span className="tick-rule mb-2 inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
              Location immobilière au Maroc
            </span>
            <h1 className="mt-4 font-display text-4xl leading-[1.1] text-[var(--color-ink)] sm:text-5xl">
              Trouvez, louez et gérez un bien, sans intermédiaire caché.
            </h1>
            <p className="mt-6 max-w-md text-base leading-relaxed text-[var(--color-ink-2)]">
              ImmoVision met en relation propriétaires et locataires partout au Maroc :
              annonces vérifiées, contrat généré automatiquement, paiements suivis et
              messagerie intégrée — du premier clic jusqu'à la signature.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/login?mode=register"
                className="inline-flex items-center gap-2 rounded-md bg-[var(--color-brass)] px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)]"
              >
                Créer un compte gratuit
                <ArrowRight size={16} />
              </Link>
              <a
                href="#catalogue"
                className="inline-flex items-center gap-2 rounded-md border border-[var(--color-line)] px-6 py-3 text-sm font-medium text-[var(--color-ink)] transition-colors hover:border-[var(--color-brass)] hover:text-[var(--color-brass-deep)]"
              >
                Voir les annonces
              </a>
            </div>

            <dl className="mt-12 grid grid-cols-3 gap-6 border-t border-[var(--color-line)] pt-6">
              <div>
                <dt className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-ink-3)]">
                  Biens en ligne
                </dt>
                <dd className="mt-1 font-display text-2xl text-[var(--color-ink)]">
                  {loadingStats ? "—" : (stats?.biens_en_ligne ?? biens.length)}
                </dd>
              </div>
              <div>
                <dt className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-ink-3)]">
                  Villes couvertes
                </dt>
                <dd className="mt-1 font-display text-2xl text-[var(--color-ink)]">
                  {loadingStats
                    ? "—"
                    : (stats?.villes_couvertes ?? new Set(biens.map((b) => b.ville)).size)}
                </dd>
              </div>
              <div>
                <dt className="font-mono text-[11px] uppercase tracking-widest text-[var(--color-ink-3)]">
                  Espaces dédiés
                </dt>
                <dd className="mt-1 font-display text-2xl text-[var(--color-ink)]">
                  {loadingStats ? "—" : (stats?.espaces_dedies ?? 3)}
                </dd>
              </div>
            </dl>
          </div>

          <div className="relative mx-auto w-full max-w-sm md:max-w-none">
            <div className="absolute -inset-4 -z-10 bg-[var(--color-brass-bg)]" style={ARCH_STYLE} />
            <div
              className="overflow-hidden border border-[var(--color-line)] shadow-xl"
              style={ARCH_STYLE}
            >
              <img
                src={hero}
                alt="Bien immobilier proposé sur ImmoVision"
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ================= SERVICES ================= */}
      <section id="services" className="border-t border-[var(--color-line)] bg-[var(--color-card)] py-20">
        <div className="mx-auto max-w-7xl px-4">
          <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
            Services
          </span>
          <h2 className="mt-4 max-w-xl font-display text-3xl text-[var(--color-ink)]">
            Tout le parcours de location, sur une seule plateforme
          </h2>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {SERVICES.map((s) => (
              <div
                key={s.title}
                className="rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] p-6 transition-shadow hover:shadow-md"
              >
                <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-md bg-[var(--color-brass-bg)] text-[var(--color-brass-deep)]">
                  <s.icon size={20} />
                </div>
                <h3 className="font-display text-base text-[var(--color-ink)]">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--color-ink-2)]">{s.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= CATALOGUE ================= */}
      <section id="catalogue" className="py-20">
        <div className="mx-auto max-w-7xl px-4">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
                Catalogue
              </span>
              <h2 className="mt-4 font-display text-3xl text-[var(--color-ink)]">
                Annonces récentes
              </h2>
            </div>
            <Link
              to="/login"
              className="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--color-brass-deep)] hover:underline"
            >
              Voir tout le catalogue
              <ArrowRight size={15} />
            </Link>
          </div>

          {loadingBiens ? (
            <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {[0, 1, 2].map((i) => (
                <div key={i} className="h-80 animate-pulse rounded-lg bg-[var(--color-paper-2)]" />
              ))}
            </div>
          ) : biens.length === 0 ? (
            <div className="mt-10 rounded-lg border border-dashed border-[var(--color-line)] p-12 text-center">
              <p className="text-sm text-[var(--color-ink-2)]">
                Aucune annonce publiée pour le moment. Créez un compte professionnel pour
                publier la première.
              </p>
              <div className="mt-4 flex justify-center">
                <PublierAnnonceButton variant="solid" />
              </div>
            </div>
          ) : (
            <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {biens.slice(0, 6).map((b) => (
                <ListingPreviewCard key={b.id} bien={b} />
              ))}
            </div>
          )}
          <p className="mt-6 text-xs text-[var(--color-ink-3)]">
            Aperçu à titre d'exemple — connectez-vous pour consulter le détail complet
            d'une annonce, contacter un propriétaire ou réserver.
          </p>
        </div>
      </section>

      {/* ================= BLOG ================= */}
      {(loadingActualites || actualites.length > 0) && (
        <section id="actualites" className="border-t border-[var(--color-line)] bg-[var(--color-card)] py-20">
          <div className="mx-auto max-w-7xl px-4">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
                  Blog
                </span>
                <h2 className="mt-4 font-display text-3xl text-[var(--color-ink)]">
                  Les derniers articles d'ImmoVision
                </h2>
              </div>
              <Link
                to="/blog"
                className="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--color-brass-deep)] hover:underline"
              >
                Voir tous les articles
                <ArrowRight size={15} />
              </Link>
            </div>

            {loadingActualites ? (
              <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-64 animate-pulse rounded-lg bg-[var(--color-paper-2)]" />
                ))}
              </div>
            ) : (
              <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                {actualites.map((a) => (
                  <article
                    key={a.id}
                    className="overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)]"
                  >
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
                    <div className="space-y-2 p-5">
                      <p className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wide text-[var(--color-brass-deep)]">
                        <CalendarDays size={12} />
                        {new Date(a.date_creation).toLocaleDateString("fr-FR", {
                          day: "numeric",
                          month: "long",
                          year: "numeric",
                        })}
                      </p>
                      <h3 className="font-display text-base leading-snug text-[var(--color-ink)]">
                        {a.titre}
                      </h3>
                      <p className="line-clamp-3 text-sm leading-relaxed text-[var(--color-ink-2)]">
                        {a.extrait || stripHtml(a.contenu_html)}
                      </p>
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
            )}
          </div>
        </section>
      )}

      {/* ================= À PROPOS ================= */}
      <section id="apropos" className="border-t border-[var(--color-line)] bg-[var(--color-card)] py-20">
        <div className="mx-auto max-w-7xl px-4">
          <div className="grid gap-12 md:grid-cols-2">
            <div>
              <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
                À propos
              </span>
              <h2 className="mt-4 font-display text-3xl text-[var(--color-ink)]">
                Une plateforme pensée pour le marché locatif marocain
              </h2>
              <p className="mt-5 text-sm leading-relaxed text-[var(--color-ink-2)]">
                ImmoVision — L’intelligence au service de l’immobilier va au-delà d’un simple site d’annonces. 
                Notre plateforme intègre nativement la gestion des contrats, des paiements et de la messagerie afin de créer un écosystème immobilier complet et intelligent.

                Chaque interaction — publication d’une annonce, réservation, signature d’un contrat ou transaction financière
                — génère des données exploitées au sein d’une architecture Big Data moderne basée sur la collecte,
                 le stockage et l’analyse massive des informations. Ces données alimentent des modèles d’intelligence artificielle capables d’améliorer continuellement l’estimation des loyers, 
                 la recommandation des biens, la détection des fraudes et l’analyse des tendances du marché immobilier.

                Grâce à cette combinaison entre Big Data, Machine Learning et automatisation intelligente,
                 ImmoVision transforme les données immobilières en décisions fiables, rapides et personnalisées pour les clients, propriétaires et professionnels du secteur.

              </p>
              <ul className="mt-6 space-y-3">
                {[
                  "Comptes propriétaires vérifiés par un administrateur avant publication",
                  "Contrat généré automatiquement à la confirmation d'une réservation",
                  "Données personnelles traitées conformément à la loi 09-08",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-[var(--color-ink-2)]">
                    <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-[var(--color-brass-deep)]" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-4">
              {ACTORS.map((a) => (
                <div
                  key={a.role}
                  className="flex gap-4 rounded-lg border border-[var(--color-line)] bg-[var(--color-paper)] p-5"
                >
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[var(--color-brass-bg)] text-[var(--color-brass-deep)]">
                    <a.icon size={20} />
                  </div>
                  <div>
                    <h3 className="font-display text-base text-[var(--color-ink)]">{a.role}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-[var(--color-ink-2)]">{a.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ================= CONTACT ================= */}
      <section id="contact" className="py-20">
        <div className="mx-auto max-w-7xl px-4">
          <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
            Contact
          </span>
          <h2 className="mt-4 font-display text-3xl text-[var(--color-ink)]">
            Une question ? Écrivez-nous
          </h2>

          <div className="mt-10 grid gap-10 md:grid-cols-[1fr_1.3fr]">
            <div className="space-y-5">
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="flex items-center gap-3 text-sm text-[var(--color-ink-2)] transition-colors hover:text-[var(--color-brass-deep)]"
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-brass-bg)] text-[var(--color-brass-deep)]">
                  <Mail size={17} />
                </span>
                {CONTACT_EMAIL}
              </a>
              <a
                href="tel:+212637808129"
                className="flex items-center gap-3 text-sm text-[var(--color-ink-2)] transition-colors hover:text-[var(--color-brass-deep)]"
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-brass-bg)] text-[var(--color-brass-deep)]">
                  <Phone size={17} />
                </span>
                +212 637808129
              </a>
              <a
                href={`https://wa.me/${WHATSAPP_NUMBER}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 text-sm text-[var(--color-ink-2)] transition-colors hover:text-[var(--color-sage)]"
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-sage-bg)] text-[var(--color-sage)]">
                  <MessageCircle size={17} />
                </span>
                Discuter sur WhatsApp
              </a>
              <div className="flex items-center gap-3 text-sm text-[var(--color-ink-2)]">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--color-brass-bg)] text-[var(--color-brass-deep)]">
                  <MapPin size={17} />
                </span>
                Kénitra, Maroc
              </div>
            </div>

            <form
              onSubmit={handleContactSubmit}
              className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-6"
            >
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Nom</label>
                  <input
                    required
                    disabled={contactSending}
                    value={contactName}
                    onChange={(e) => setContactName(e.target.value)}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)] disabled:opacity-60"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Email</label>
                  <input
                    required
                    type="email"
                    disabled={contactSending}
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)] disabled:opacity-60"
                  />
                </div>
              </div>
              <label className="mb-1 mt-4 block text-xs font-medium text-[var(--color-ink-2)]">Message</label>
              <textarea
                required
                rows={4}
                disabled={contactSending}
                value={contactMessage}
                onChange={(e) => setContactMessage(e.target.value)}
                className="w-full resize-none rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)] focus:ring-1 focus:ring-[var(--color-brass)] disabled:opacity-60"
              />
              <button
                type="submit"
                disabled={contactSending}
                className="mt-4 inline-flex items-center gap-2 rounded-md bg-[var(--color-brass)] px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)] disabled:cursor-not-allowed disabled:opacity-70"
              >
                {contactSending ? (
                  <>
                    <Loader2 size={15} className="animate-spin" />
                    Envoi en cours…
                  </>
                ) : (
                  <>
                    <Send size={15} />
                    Envoyer le message
                  </>
                )}
              </button>
              {contactSent && (
                <p className="mt-3 text-xs text-[var(--color-sage)]">
                  Message envoyé — nous vous répondrons rapidement à {contactEmail || "votre adresse"}.
                </p>
              )}
              {contactError && (
                <p className="mt-3 text-xs text-[var(--color-rust)]">{contactError}</p>
              )}
            </form>
          </div>
        </div>
      </section>

      {/* ================= FOOTER ================= */}
      <SiteFooter />
    </div>
  );
}

import SiteFooter from "../components/layout/SiteFooter";
import SiteHeader from "../components/layout/SiteHeader";

/**
 * Page publique — Foire aux questions.
 * Mélange de questions générales sur la location/vente immobilière au Maroc
 * et de questions spécifiques au fonctionnement d'ImmoVision. Le balisage
 * schema.org FAQPage (JSON-LD ci-dessous) aide les moteurs de réponse
 * (IA + Google) à extraire directement les paires question/réponse.
 * Voir aussi PolitiqueQualitePage.tsx (même patron visuel).
 */

const faqItems = [
  {
    question: "Quels documents faut-il pour louer un appartement au Maroc ?",
    reponse:
      "En général : une pièce d'identité (CIN ou passeport pour un étranger), un justificatif de revenus ou de solvabilité, et parfois un garant. Le propriétaire ou l'agence peut demander des documents complémentaires selon le bien. Sur ImmoVision, ces échanges se font directement via la messagerie intégrée avec le propriétaire.",
  },
  {
    question: "Quelle est la durée standard d'un bail de location au Maroc ?",
    reponse:
      "Il n'existe pas de durée unique imposée : les baux d'habitation sont le plus souvent conclus pour une durée d'un an, renouvelable par tacite reconduction, mais la durée exacte et les conditions de renouvellement ou de résiliation doivent être précisées dans le contrat signé entre les deux parties.",
  },
  {
    question: "Faut-il verser un dépôt de garantie pour louer un bien ?",
    reponse:
      "Un dépôt de garantie (souvent appelé caution) est une pratique courante pour couvrir d'éventuels dégâts ou loyers impayés. Son montant et ses conditions de restitution en fin de bail doivent être clairement indiqués dans le contrat de location avant la signature.",
  },
  {
    question: "Comment fonctionne l'estimation de prix par intelligence artificielle sur ImmoVision ?",
    reponse:
      "Le modèle d'estimation analyse les caractéristiques du bien (ville, quartier, superficie, type) et les compare à des données de marché pour proposer une fourchette de prix indicative. C'est une aide à la décision pour le propriétaire au moment de la publication, pas une expertise immobilière officielle.",
  },
  {
    question: "Comment ImmoVision vérifie-t-il les annonces et les propriétaires ?",
    reponse:
      "Les comptes propriétaires professionnels (agence, promoteur, conciergerie) sont examinés par l'équipe ImmoVision avant de pouvoir publier. Chaque annonce peut aussi être passée au crible d'un module de détection de fraude qui repère les écarts de prix anormaux, en complément d'une modération humaine.",
  },
  {
    question: "Comment se passe le paiement et le contrat sur la plateforme ?",
    reponse:
      "Lorsqu'un propriétaire confirme une réservation, un contrat est généré automatiquement avec les informations de la location (loyer, dates). Les paiements liés à ce contrat sont suivis et tracés directement dans l'espace personnel du client et du propriétaire.",
  },
  {
    question: "Comment contacter un propriétaire ou signaler un problème ?",
    reponse:
      "Chaque annonce dispose d'un bouton pour démarrer une conversation directe avec le propriétaire via la messagerie intégrée. En cas de litige, une réclamation peut être déposée depuis la plateforme ; elle est transmise immédiatement à l'équipe ImmoVision et au propriétaire concerné.",
  },
  {
    question: "ImmoVision est-elle disponible dans toutes les villes du Maroc ?",
    reponse:
      "ImmoVision référence des annonces de location et de vente à travers le Maroc, avec une recherche filtrable par ville et affichage sur carte interactive. Le nombre d'annonces disponibles varie selon les villes.",
  },
];

const faqJsonLd = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: faqItems.map((item) => ({
    "@type": "Question",
    name: item.question,
    acceptedAnswer: {
      "@type": "Answer",
      text: item.reponse,
    },
  })),
};

export default function FaqPage() {
  return (
    <div className="min-h-screen bg-[var(--color-paper)]">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-6 py-16">
        <span className="tick-rule inline-block font-mono text-xs uppercase tracking-[0.2em] text-[var(--color-brass-deep)]">
          Questions fréquentes
        </span>
        <h1 className="mt-4 font-display text-3xl text-[var(--color-ink)] sm:text-4xl">
          Foire aux questions
        </h1>
        <p className="mt-2 text-sm text-[var(--color-ink-2)]">
          Location, vente immobilière au Maroc et fonctionnement d'ImmoVision.
        </p>
        <div className="mt-8 space-y-6 text-sm leading-relaxed text-[var(--color-ink-2)]">
          {faqItems.map((item) => (
            <section key={item.question}>
              <h2 className="mb-2 font-display text-lg text-[var(--color-ink)]">
                {item.question}
              </h2>
              <p>{item.reponse}</p>
            </section>
          ))}
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}

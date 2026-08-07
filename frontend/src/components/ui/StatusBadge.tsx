type Tone = "sage" | "brass" | "rust" | "neutral";

const TONE_STYLES: Record<Tone, string> = {
  sage: "bg-[var(--color-sage-bg)] text-[var(--color-sage)]",
  brass: "bg-[#f4e9df] text-[var(--color-brass-deep)]",
  rust: "bg-[var(--color-rust-bg)] text-[var(--color-rust)]",
  neutral: "bg-[var(--color-paper-2)] text-[var(--color-ink-2)]",
};

const STATUS_TONE: Record<string, Tone> = {
  disponible: "sage",
  acceptee: "sage",
  paye: "sage",
  reussi: "sage",
  signe: "sage",
  resolue: "sage",
  confirmee: "sage",
  en_attente: "brass",
  en_cours: "brass",
  brouillon: "brass",
  loue: "neutral",
  vendu: "neutral",
  rembourse: "neutral",
  suspendu: "rust",
  refusee: "rust",
  annulee: "rust",
  echoue: "rust",
  rejetee: "rust",
  resilie: "rust",
  ouverte: "rust",
};

const LABELS: Record<string, string> = {
  disponible: "Disponible",
  loue: "Loué",
  vendu: "Vendu",
  en_attente: "En attente",
  suspendu: "Suspendu",
  acceptee: "Acceptée",
  confirmee: "Confirmée",
  refusee: "Refusée",
  annulee: "Annulée",
  signe: "Signé",
  resilie: "Résilié",
  expire: "Expiré",
  paye: "Payé",
  reussi: "Payé",
  echoue: "Échoué",
  rembourse: "Remboursé",
  ouverte: "Ouverte",
  en_cours: "En cours",
  resolue: "Résolue",
  rejetee: "Rejetée",
};

export default function StatusBadge({ status }: { status: string }) {
  const tone = STATUS_TONE[status] ?? "neutral";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium font-mono tracking-wide uppercase ${TONE_STYLES[tone]}`}
    >
      {LABELS[status] ?? status}
    </span>
  );
}

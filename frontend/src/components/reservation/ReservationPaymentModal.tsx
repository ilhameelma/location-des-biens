import { useEffect, useState } from "react";
import {
  X,
  CreditCard,
  Landmark,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  AlertTriangle,
  CalendarClock,
} from "lucide-react";
import { api } from "../../lib/api";
import type { Bien, MethodePaiementInstantane, Reservation } from "../../types";

type Etape = "recap" | "methode" | "details" | "traitement" | "succes" | "erreur";

const AUJOURD_HUI = new Date().toISOString().slice(0, 10);

function formatNumeroCarte(value: string): string {
  const chiffres = value.replace(/\D/g, "").slice(0, 16);
  return chiffres.replace(/(.{4})/g, "$1 ").trim();
}

function formatExpiration(value: string): string {
  const chiffres = value.replace(/\D/g, "").slice(0, 4);
  if (chiffres.length <= 2) return chiffres;
  return `${chiffres.slice(0, 2)}/${chiffres.slice(2)}`;
}

function formatDateHeure(iso: string): string {
  return new Date(iso).toLocaleString("fr-MA", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ReservationPaymentModal({
  bien,
  onClose,
  onSuccess,
}: {
  bien: Bien | null;
  onClose: () => void;
  onSuccess: (reservation: Reservation) => void;
}) {
  const [etape, setEtape] = useState<Etape>("recap");
  const [dateDebut, setDateDebut] = useState(AUJOURD_HUI);
  const [dateFin, setDateFin] = useState("");
  const [methode, setMethode] = useState<MethodePaiementInstantane>("carte_bancaire");

  const [numeroCarte, setNumeroCarte] = useState("");
  const [nomCarte, setNomCarte] = useState("");
  const [expiration, setExpiration] = useState("");
  const [cvv, setCvv] = useState("");

  const [erreur, setErreur] = useState<string | null>(null);
  const [reservationCreee, setReservationCreee] = useState<Reservation | null>(null);

  // Réinitialise le formulaire à chaque nouvelle ouverture (nouveau bien).
  useEffect(() => {
    if (bien) {
      setEtape("recap");
      setDateDebut(AUJOURD_HUI);
      setDateFin("");
      setMethode("carte_bancaire");
      setNumeroCarte("");
      setNomCarte("");
      setExpiration("");
      setCvv("");
      setErreur(null);
      setReservationCreee(null);
    }
  }, [bien]);

  if (!bien) return null;

  const carteValide =
    numeroCarte.replace(/\D/g, "").length === 16 &&
    nomCarte.trim().length >= 3 &&
    /^\d{2}\/\d{2}$/.test(expiration) &&
    /^\d{3,4}$/.test(cvv);

  function fermerSiPossible() {
    if (etape === "traitement") return; // pas d'annulation pendant le paiement simulé
    onClose();
  }

  async function lancerPaiement() {
    if (!bien) return;
    setEtape("traitement");
    setErreur(null);

    const referenceTransaction =
      methode === "carte_bancaire"
        ? `**** ${numeroCarte.replace(/\D/g, "").slice(-4)}`
        : `VIR-${Date.now().toString(36).toUpperCase()}`;

    // Simule le temps de traitement d'un vrai prestataire de paiement —
    // aucune donnée de carte n'est envoyée au back-end, seule une
    // référence masquée l'est (voir ReservationInstantaneeCreate côté API).
    await new Promise((resolve) => setTimeout(resolve, 1400));

    try {
      const reservation = await api.post<Reservation>("/reservations/instantanee", {
        bien_id: bien.id,
        date_debut: dateDebut,
        date_fin: dateFin || undefined,
        methode_paiement: methode,
        reference_transaction: referenceTransaction,
      });
      setReservationCreee(reservation);
      setEtape("succes");
      onSuccess(reservation);
    } catch (err) {
      setErreur(err instanceof Error ? err.message : "Le paiement a échoué, réessayez.");
      setEtape("erreur");
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={fermerSiPossible}
    >
      <div
        className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg bg-[var(--color-card)] shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* En-tête */}
        <div className="flex items-center justify-between border-b border-[var(--color-line)] px-5 py-4">
          <div>
            <h2 className="font-display text-lg text-[var(--color-ink)]">
              {etape === "succes" ? "Réservation confirmée" : "Réserver et payer"}
            </h2>
            <p className="text-xs text-[var(--color-ink-3)]">{bien.titre}</p>
          </div>
          {etape !== "traitement" && (
            <button
              onClick={onClose}
              aria-label="Fermer"
              className="rounded-full p-1.5 text-[var(--color-ink-3)] hover:bg-[var(--color-paper-2)] hover:text-[var(--color-ink)]"
            >
              <X size={18} />
            </button>
          )}
        </div>

        <div className="p-5">
          {/* ---------- Étape 1 : récapitulatif + dates ---------- */}
          {etape === "recap" && (
            <div className="space-y-4">
              <div className="flex items-baseline justify-between rounded-md bg-[var(--color-paper-2)] px-3 py-2">
                <span className="text-sm text-[var(--color-ink-2)]">Montant du loyer</span>
                <span className="font-mono text-base font-semibold text-[var(--color-ink)]">
                  {bien.prix.toLocaleString("fr-MA")} MAD
                </span>
              </div>
              <div>
                <label className="block text-xs text-[var(--color-ink-3)]">Date de début</label>
                <input
                  type="date"
                  value={dateDebut}
                  min={AUJOURD_HUI}
                  onChange={(e) => setDateDebut(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-[var(--color-ink-3)]">
                  Date de fin (optionnel)
                </label>
                <input
                  type="date"
                  value={dateFin}
                  min={dateDebut}
                  onChange={(e) => setDateFin(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm"
                />
              </div>
              <button
                onClick={() => setEtape("methode")}
                className="w-full rounded-md bg-[var(--color-brass)] py-2.5 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)]"
              >
                Continuer
              </button>
            </div>
          )}

          {/* ---------- Étape 2 : choix du mode de paiement ---------- */}
          {etape === "methode" && (
            <div className="space-y-3">
              <p className="text-xs text-[var(--color-ink-3)]">Choisissez un mode de paiement</p>
              <button
                onClick={() => setMethode("carte_bancaire")}
                className={`flex w-full items-center gap-3 rounded-md border p-3 text-left transition-colors ${
                  methode === "carte_bancaire"
                    ? "border-[var(--color-brass)] bg-[var(--color-brass-bg)]"
                    : "border-[var(--color-line)] hover:bg-[var(--color-paper-2)]"
                }`}
              >
                <CreditCard size={20} className="text-[var(--color-brass-deep)]" />
                <div>
                  <div className="text-sm font-medium text-[var(--color-ink)]">Carte bancaire</div>
                  <div className="text-xs text-[var(--color-ink-3)]">Débit immédiat</div>
                </div>
              </button>
              <button
                onClick={() => setMethode("virement")}
                className={`flex w-full items-center gap-3 rounded-md border p-3 text-left transition-colors ${
                  methode === "virement"
                    ? "border-[var(--color-brass)] bg-[var(--color-brass-bg)]"
                    : "border-[var(--color-line)] hover:bg-[var(--color-paper-2)]"
                }`}
              >
                <Landmark size={20} className="text-[var(--color-brass-deep)]" />
                <div>
                  <div className="text-sm font-medium text-[var(--color-ink)]">Virement bancaire</div>
                  <div className="text-xs text-[var(--color-ink-3)]">Confirmation immédiate simulée</div>
                </div>
              </button>
              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => setEtape("recap")}
                  className="flex-1 rounded-md border border-[var(--color-line)] py-2 text-sm text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                >
                  Retour
                </button>
                <button
                  onClick={() => setEtape("details")}
                  className="flex-1 rounded-md bg-[var(--color-brass)] py-2 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)]"
                >
                  Continuer
                </button>
              </div>
            </div>
          )}

          {/* ---------- Étape 3 : détails du paiement ---------- */}
          {etape === "details" && methode === "carte_bancaire" && (
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-[var(--color-ink-3)]">Numéro de carte</label>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="1234 5678 9012 3456"
                  value={numeroCarte}
                  onChange={(e) => setNumeroCarte(formatNumeroCarte(e.target.value))}
                  className="mt-1 w-full rounded-md border border-[var(--color-line)] px-3 py-2 font-mono text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-[var(--color-ink-3)]">Nom du titulaire</label>
                <input
                  type="text"
                  placeholder="Nom Prénom"
                  value={nomCarte}
                  onChange={(e) => setNomCarte(e.target.value)}
                  className="mt-1 w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm"
                />
              </div>
              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="block text-xs text-[var(--color-ink-3)]">Expiration</label>
                  <input
                    type="text"
                    inputMode="numeric"
                    placeholder="MM/AA"
                    value={expiration}
                    onChange={(e) => setExpiration(formatExpiration(e.target.value))}
                    className="mt-1 w-full rounded-md border border-[var(--color-line)] px-3 py-2 font-mono text-sm"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-xs text-[var(--color-ink-3)]">CVV</label>
                  <input
                    type="password"
                    inputMode="numeric"
                    placeholder="123"
                    value={cvv}
                    onChange={(e) => setCvv(e.target.value.replace(/\D/g, "").slice(0, 4))}
                    className="mt-1 w-full rounded-md border border-[var(--color-line)] px-3 py-2 font-mono text-sm"
                  />
                </div>
              </div>
              <p className="flex items-center gap-1.5 text-xs text-[var(--color-ink-3)]">
                <ShieldCheck size={13} /> Paiement simulé à des fins de démonstration (PFE) — aucune
                donnée bancaire réelle n'est traitée.
              </p>
              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => setEtape("methode")}
                  className="flex-1 rounded-md border border-[var(--color-line)] py-2 text-sm text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                >
                  Retour
                </button>
                <button
                  onClick={lancerPaiement}
                  disabled={!carteValide}
                  className="flex-1 rounded-md bg-[var(--color-brass)] py-2 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-50"
                >
                  Payer {bien.prix.toLocaleString("fr-MA")} MAD
                </button>
              </div>
            </div>
          )}

          {etape === "details" && methode === "virement" && (
            <div className="space-y-3">
              <div className="rounded-md border border-[var(--color-line)] bg-[var(--color-paper-2)] p-3 font-mono text-xs text-[var(--color-ink-2)]">
                <div>Bénéficiaire : SmartRent Platform SARL</div>
                <div>IBAN : MA64 0000 0000 0000 0000 0000 000</div>
                <div>Référence à indiquer : RES-{bien.id.slice(0, 8).toUpperCase()}</div>
              </div>
              <p className="text-xs text-[var(--color-ink-3)]">
                Effectuez le virement depuis votre application bancaire, puis confirmez ci-dessous —
                dans ce projet de démonstration, la confirmation est immédiate.
              </p>
              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => setEtape("methode")}
                  className="flex-1 rounded-md border border-[var(--color-line)] py-2 text-sm text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                >
                  Retour
                </button>
                <button
                  onClick={lancerPaiement}
                  className="flex-1 rounded-md bg-[var(--color-brass)] py-2 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)]"
                >
                  J'ai effectué le virement
                </button>
              </div>
            </div>
          )}

          {/* ---------- Étape 4 : traitement ---------- */}
          {etape === "traitement" && (
            <div className="flex flex-col items-center gap-3 py-10 text-center">
              <Loader2 size={28} className="animate-spin text-[var(--color-brass)]" />
              <p className="text-sm text-[var(--color-ink-2)]">Traitement du paiement en cours…</p>
            </div>
          )}

          {/* ---------- Étape 5 : succès ---------- */}
          {etape === "succes" && reservationCreee && (
            <div className="space-y-4 text-center">
              <div className="flex flex-col items-center gap-2 py-2">
                <CheckCircle2 size={40} className="text-[var(--color-sage)]" />
                <p className="text-sm text-[var(--color-ink)]">
                  Paiement réussi — votre réservation est confirmée.
                </p>
              </div>
              <div className="rounded-md bg-[var(--color-paper-2)] px-3 py-2 text-left text-sm">
                <div className="flex justify-between">
                  <span className="text-[var(--color-ink-3)]">Montant payé</span>
                  <span className="font-mono font-medium text-[var(--color-ink)]">
                    {bien.prix.toLocaleString("fr-MA")} MAD
                  </span>
                </div>
              </div>
              {reservationCreee.date_limite_annulation && (
                <div className="flex items-start gap-2 rounded-md bg-[var(--color-brass-bg)] px-3 py-2 text-left text-xs text-[var(--color-brass-deep)]">
                  <CalendarClock size={14} className="mt-0.5 shrink-0" />
                  <span>
                    Annulation gratuite avec remboursement possible jusqu'au{" "}
                    {formatDateHeure(reservationCreee.date_limite_annulation)}, depuis « Mes
                    réservations ».
                  </span>
                </div>
              )}
              <button
                onClick={onClose}
                className="w-full rounded-md bg-[var(--color-brass)] py-2.5 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)]"
              >
                Fermer
              </button>
            </div>
          )}

          {/* ---------- Erreur ---------- */}
          {etape === "erreur" && (
            <div className="space-y-4 text-center">
              <div className="flex flex-col items-center gap-2 py-2">
                <AlertTriangle size={32} className="text-[var(--color-rust)]" />
                <p className="text-sm text-[var(--color-rust)]">{erreur}</p>
              </div>
              <button
                onClick={() => setEtape("details")}
                className="w-full rounded-md bg-[var(--color-brass)] py-2.5 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)]"
              >
                Réessayer
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

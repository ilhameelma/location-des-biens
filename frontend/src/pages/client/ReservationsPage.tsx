import { Fragment, useEffect, useMemo, useState } from "react";
import { CreditCard, Clock, CheckCircle2, Undo2 } from "lucide-react";
import { api } from "../../lib/api";
import type { Bien, Reservation } from "../../types";
import StatusBadge from "../../components/ui/StatusBadge";

const METHODES = [
  { value: "carte_bancaire", label: "Carte bancaire" },
  { value: "virement", label: "Virement" },
  { value: "especes", label: "Espèces" },
];

// Recalcule les comptes à rebours toutes les 30s — pas besoin de plus
// fréquent, il ne s'agit que d'un affichage indicatif (la décision
// d'annulation/expiration elle-même est prise côté serveur, voir
// backend/app/paiement_expiration.py et routers/reservations.py).
const INTERVALLE_RAFRAICHISSEMENT_MS = 30_000;

function formatCompteARebours(dateLimiteIso: string, maintenant: number, suffixe: string): string {
  const restantMs = new Date(dateLimiteIso).getTime() - maintenant;
  if (restantMs <= 0) return "Délai dépassé";
  const heures = Math.floor(restantMs / (1000 * 60 * 60));
  const minutes = Math.floor((restantMs % (1000 * 60 * 60)) / (1000 * 60));
  if (heures >= 1) return `${heures}h ${minutes.toString().padStart(2, "0")}min restantes ${suffixe}`;
  return `${minutes} min restantes ${suffixe}`;
}

export default function ReservationsPage() {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [biens, setBiens] = useState<Record<string, Bien>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Formulaire de paiement inline (ancien flux "payer après confirmation" —
  // une seule réservation ouverte à la fois)
  const [paiementOuvertPour, setPaiementOuvertPour] = useState<string | null>(null);
  const [methode, setMethode] = useState(METHODES[0].value);
  const [paiementEnCours, setPaiementEnCours] = useState(false);
  const [paiementErreur, setPaiementErreur] = useState<string | null>(null);

  // Annulation gratuite (réservation payée instantanément, fenêtre de 24h)
  const [annulationEnCours, setAnnulationEnCours] = useState<string | null>(null);
  const [annulationErreur, setAnnulationErreur] = useState<string | null>(null);

  const [maintenant, setMaintenant] = useState(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => setMaintenant(Date.now()), INTERVALLE_RAFRAICHISSEMENT_MS);
    return () => clearInterval(timer);
  }, []);

  const fetchAll = () => {
    setLoading(true);
    api
      .get<Reservation[]>("/reservations/me")
      .then(async (res) => {
        setReservations(res);
        const uniqueBienIds = [...new Set(res.map((r) => r.bien_id))];
        const biensList = await Promise.all(
          uniqueBienIds.map((id) => api.get<Bien>(`/biens/${id}`).catch(() => null))
        );
        const map: Record<string, Bien> = {};
        biensList.forEach((b) => {
          if (b) map[b.id] = b;
        });
        setBiens(map);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchAll, []);

  function reservationEnAttentePaiement(r: Reservation): boolean {
    return r.statut === "confirmee" && r.paiement_effectue === false && !!r.contrat_id && !!r.date_limite_paiement;
  }

  const nbEnAttentePaiement = useMemo(
    () => reservations.filter(reservationEnAttentePaiement).length,
    [reservations]
  );

  const nbAnnulables = useMemo(() => reservations.filter((r) => r.peut_annuler).length, [reservations]);

  function ouvrirPaiement(r: Reservation) {
    setPaiementOuvertPour(r.id);
    setMethode(METHODES[0].value);
    setPaiementErreur(null);
  }

  async function confirmerPaiement(r: Reservation) {
    if (!r.contrat_id || !r.montant_a_payer) return;
    setPaiementEnCours(true);
    setPaiementErreur(null);
    try {
      await api.post("/paiements", {
        contrat_id: r.contrat_id,
        montant: r.montant_a_payer,
        methode,
      });
      setReservations((prev) =>
        prev.map((res) => (res.id === r.id ? { ...res, paiement_effectue: true } : res))
      );
      setPaiementOuvertPour(null);
    } catch (err) {
      setPaiementErreur(err instanceof Error ? err.message : "Échec du paiement, réessayez.");
    } finally {
      setPaiementEnCours(false);
    }
  }

  async function annulerReservation(r: Reservation) {
    const bien = biens[r.bien_id];
    const confirme = window.confirm(
      `Annuler votre réservation pour « ${bien?.titre ?? "ce bien"} » et être remboursé de ` +
        `${(r.montant_a_payer ?? 0).toLocaleString("fr-MA")} MAD ? Cette action est définitive.`
    );
    if (!confirme) return;

    setAnnulationEnCours(r.id);
    setAnnulationErreur(null);
    try {
      const updated = await api.post<Reservation>(`/reservations/${r.id}/annuler`, {});
      setReservations((prev) => prev.map((res) => (res.id === r.id ? updated : res)));
    } catch (err) {
      setAnnulationErreur(err instanceof Error ? err.message : "Impossible d'annuler cette réservation.");
    } finally {
      setAnnulationEnCours(null);
    }
  }

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Mes réservations</h1>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {annulationErreur && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {annulationErreur}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}

      {!loading && nbEnAttentePaiement > 0 && (
        <div className="mt-4 flex items-start gap-2 rounded-md bg-[var(--color-rust-bg)] px-4 py-3 text-sm text-[var(--color-rust)]">
          <Clock size={16} className="mt-0.5 shrink-0" />
          <span>
            {nbEnAttentePaiement === 1
              ? "1 réservation confirmée est en attente de paiement."
              : `${nbEnAttentePaiement} réservations confirmées sont en attente de paiement.`}{" "}
            Passé le délai indiqué, elle{nbEnAttentePaiement > 1 ? "s sont" : " est"} annulée
            automatiquement.
          </span>
        </div>
      )}

      {!loading && nbAnnulables > 0 && (
        <div className="mt-4 flex items-start gap-2 rounded-md bg-[var(--color-brass-bg)] px-4 py-3 text-sm text-[var(--color-brass-deep)]">
          <Undo2 size={16} className="mt-0.5 shrink-0" />
          <span>
            {nbAnnulables === 1
              ? "1 réservation payée peut encore être annulée gratuitement, avec remboursement."
              : `${nbAnnulables} réservations payées peuvent encore être annulées gratuitement, avec remboursement.`}
          </span>
        </div>
      )}

      {!loading && reservations.length === 0 && !error && (
        <p className="mt-6 text-sm text-[var(--color-ink-3)]">
          Aucune réservation pour le moment. Cherche un bien dans « Rechercher » pour en faire une.
        </p>
      )}

      {reservations.length > 0 && (
        <div className="mt-8 overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)]">
          <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-[var(--color-paper-2)] font-mono text-xs uppercase tracking-wide text-[var(--color-ink-2)]">
              <tr>
                <th className="px-4 py-3">Bien</th>
                <th className="px-4 py-3">Ville</th>
                <th className="px-4 py-3">Date de début</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {reservations.map((r) => {
                const bien = biens[r.bien_id];
                const enAttente = reservationEnAttentePaiement(r);
                const formulaireOuvert = paiementOuvertPour === r.id;
                return (
                  <Fragment key={r.id}>
                    <tr key={r.id} className="border-t border-[var(--color-line)]">
                      <td className="px-4 py-3 font-medium text-[var(--color-ink)]">
                        {bien?.titre ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-[var(--color-ink-2)]">{bien?.ville ?? "—"}</td>
                      <td className="px-4 py-3 font-mono text-[var(--color-ink-2)]">{r.date_debut}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <StatusBadge status={r.statut} />
                          {r.statut === "confirmee" && r.paiement_effectue === true && (
                            <span className="inline-flex items-center gap-1 text-xs text-[var(--color-sage)]">
                              <CheckCircle2 size={13} /> Payé
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          {enAttente && !formulaireOuvert && (
                            <button
                              onClick={() => ouvrirPaiement(r)}
                              className="inline-flex items-center gap-1.5 rounded-md bg-[var(--color-brass)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--color-brass-deep)]"
                            >
                              <CreditCard size={13} />
                              Payer maintenant
                            </button>
                          )}
                          {r.peut_annuler && (
                            <button
                              onClick={() => annulerReservation(r)}
                              disabled={annulationEnCours === r.id}
                              className="inline-flex items-center gap-1.5 rounded-md border border-[var(--color-rust)] px-3 py-1.5 text-xs font-medium text-[var(--color-rust)] hover:bg-[var(--color-rust-bg)] disabled:opacity-50"
                            >
                              <Undo2 size={13} />
                              {annulationEnCours === r.id ? "Annulation…" : "Annuler et être remboursé"}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                    {enAttente && (
                      <tr key={`${r.id}-info`} className="border-t border-[var(--color-line)] bg-[var(--color-paper-2)]">
                        <td colSpan={5} className="px-4 py-2 text-xs text-[var(--color-ink-3)]">
                          {r.date_limite_paiement &&
                            formatCompteARebours(r.date_limite_paiement, maintenant, "pour payer")}
                        </td>
                      </tr>
                    )}
                    {r.peut_annuler && r.date_limite_annulation && (
                      <tr
                        key={`${r.id}-annulation`}
                        className="border-t border-[var(--color-line)] bg-[var(--color-brass-bg)]"
                      >
                        <td colSpan={5} className="px-4 py-2 text-xs text-[var(--color-brass-deep)]">
                          {formatCompteARebours(
                            r.date_limite_annulation,
                            maintenant,
                            "pour annuler gratuitement avec remboursement"
                          )}
                        </td>
                      </tr>
                    )}
                    {formulaireOuvert && (
                      <tr key={`${r.id}-form`} className="border-t border-[var(--color-line)]">
                        <td colSpan={5} className="px-4 py-4">
                          <div className="flex flex-wrap items-end gap-3 rounded-md border border-[var(--color-line)] bg-[var(--color-paper-2)] p-3">
                            <div>
                              <label className="block text-xs text-[var(--color-ink-3)]">Montant</label>
                              <div className="mt-1 font-mono text-base text-[var(--color-ink)]">
                                {(r.montant_a_payer ?? 0).toLocaleString("fr-MA")} MAD
                              </div>
                            </div>
                            <div>
                              <label className="block text-xs text-[var(--color-ink-3)]">Méthode</label>
                              <select
                                value={methode}
                                onChange={(e) => setMethode(e.target.value)}
                                className="mt-1 rounded-md border border-[var(--color-line)] bg-[var(--color-card)] px-2 py-1.5 text-sm"
                              >
                                {METHODES.map((m) => (
                                  <option key={m.value} value={m.value}>
                                    {m.label}
                                  </option>
                                ))}
                              </select>
                            </div>
                            <button
                              onClick={() => confirmerPaiement(r)}
                              disabled={paiementEnCours}
                              className="rounded-md bg-[var(--color-brass)] px-4 py-1.5 text-sm font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
                            >
                              {paiementEnCours ? "Paiement en cours…" : "Confirmer le paiement"}
                            </button>
                            <button
                              onClick={() => setPaiementOuvertPour(null)}
                              disabled={paiementEnCours}
                              className="rounded-md px-3 py-1.5 text-sm text-[var(--color-ink-3)] hover:text-[var(--color-ink)]"
                            >
                              Annuler
                            </button>
                          </div>
                          {paiementErreur && (
                            <p className="mt-2 text-xs text-[var(--color-rust)]">{paiementErreur}</p>
                          )}
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
          </div>
        </div>
      )}
    </div>
  );
}

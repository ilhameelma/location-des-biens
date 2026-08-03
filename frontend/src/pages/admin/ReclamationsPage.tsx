import { useEffect, useState } from "react";
import { User, Home, Mail, Phone, CheckCircle2, XCircle, Clock, Trash2, TriangleAlert } from "lucide-react";
import { api } from "../../lib/api";
import type { Reclamation, StatutReclamation } from "../../types";
import StatusBadge from "../../components/ui/StatusBadge";

// Doit rester synchronisé avec SEUIL_RECLAMATIONS_ANNONCE côté back-end
// (backend/app/routers/reclamations.py) — uniquement pour l'affichage
// (surlignage du badge), le vrai seuil qui déclenche l'alerte est appliqué
// côté serveur.
const SEUIL_RECLAMATIONS_ANNONCE = 20;

const TYPE_LABELS: Record<string, string> = {
  annonce_trompeuse: "Annonce trompeuse",
  prix_incorrect: "Prix incorrect / non respecté",
  bien_indisponible: "Bien déjà indisponible",
  comportement_proprietaire: "Comportement du propriétaire",
  autre: "Autre",
};

// Prochain statut "logique" pour le bouton principal, et actions secondaires
// (rejeter) proposées dès qu'une réclamation n'est pas encore clôturée.
const NEXT_STATUT: Record<StatutReclamation, StatutReclamation | null> = {
  ouverte: "en_cours",
  en_cours: "resolue",
  resolue: null,
  rejetee: null,
};

const NEXT_LABEL: Record<string, string> = {
  en_cours: "Prendre en charge",
  resolue: "Marquer résolue",
};

export default function ReclamationsPage() {
  const [reclamations, setReclamations] = useState<Reclamation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);
  const [deletingBien, setDeletingBien] = useState<string | null>(null);

  const fetchAll = () => {
    setLoading(true);
    api
      .get<Reclamation[]>("/reclamations")
      .then(setReclamations)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchAll, []);

  const changeStatut = async (r: Reclamation, statut: StatutReclamation) => {
    setUpdating(r.id);
    setError(null);
    try {
      await api.patch(`/reclamations/${r.id}/statut`, { statut });
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de mettre à jour");
    } finally {
      setUpdating(null);
    }
  };

  const supprimerAnnonce = async (bienId: string, titre: string | null | undefined) => {
    const confirmed = window.confirm(
      `Supprimer définitivement l'annonce « ${titre ?? bienId} » ?\n\n` +
        `Cette action est irréversible (photos et réservations liées supprimées aussi).`,
    );
    if (!confirmed) return;

    setDeletingBien(bienId);
    setError(null);
    try {
      await api.del(`/biens/${bienId}`);
      fetchAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de supprimer cette annonce");
    } finally {
      setDeletingBien(null);
    }
  };

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Réclamations</h1>
      <p className="mt-1 text-sm text-[var(--color-ink-3)]">
        Signalements déposés par les clients — traitez-les en prenant en charge, puis en
        résolvant ou en rejetant.
      </p>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}
      {!loading && reclamations.length === 0 && !error && (
        <p className="mt-6 text-sm text-[var(--color-ink-3)]">Aucune réclamation.</p>
      )}

      <div className="mt-8 space-y-4">
        {reclamations.map((r) => {
          const next = NEXT_STATUT[r.statut];
          const closed = r.statut === "resolue" || r.statut === "rejetee";
          const clientNomComplet = [r.client_prenom, r.client_nom].filter(Boolean).join(" ") || "Client inconnu";
          const proprietaireNomComplet =
            [r.proprietaire_prenom, r.proprietaire_nom].filter(Boolean).join(" ") || null;

          return (
            <div key={r.id} className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4">
              {/* En-tête : motif + statut */}
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-medium text-[var(--color-ink)]">
                  {TYPE_LABELS[r.type_reclamation] ?? r.type_reclamation}
                </span>
                <StatusBadge status={r.statut} />
              </div>

              {/* Qui réclame contre qui, à propos de quelle annonce */}
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <div className="rounded-md border border-[var(--color-line)] bg-[var(--color-paper-2)] p-3">
                  <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-[var(--color-ink-3)]">
                    <User size={13} /> Plaignant (client)
                  </p>
                  <p className="mt-1 text-sm font-medium text-[var(--color-ink)]">{clientNomComplet}</p>
                  {r.client_email && (
                    <p className="mt-0.5 flex items-center gap-1 text-xs text-[var(--color-ink-3)]">
                      <Mail size={11} /> {r.client_email}
                    </p>
                  )}
                  {r.client_telephone && (
                    <p className="mt-0.5 flex items-center gap-1 text-xs text-[var(--color-ink-3)]">
                      <Phone size={11} /> {r.client_telephone}
                    </p>
                  )}
                </div>

                <div className="rounded-md border border-[var(--color-line)] bg-[var(--color-paper-2)] p-3">
                  <p className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-[var(--color-ink-3)]">
                    <User size={13} /> Propriétaire visé
                  </p>
                  {proprietaireNomComplet ? (
                    <>
                      <p className="mt-1 text-sm font-medium text-[var(--color-ink)]">{proprietaireNomComplet}</p>
                      {r.proprietaire_email && (
                        <p className="mt-0.5 flex items-center gap-1 text-xs text-[var(--color-ink-3)]">
                          <Mail size={11} /> {r.proprietaire_email}
                        </p>
                      )}
                      {r.proprietaire_telephone && (
                        <p className="mt-0.5 flex items-center gap-1 text-xs text-[var(--color-ink-3)]">
                          <Phone size={11} /> {r.proprietaire_telephone}
                        </p>
                      )}
                    </>
                  ) : (
                    <p className="mt-1 text-sm text-[var(--color-ink-3)]">
                      Aucune annonce liée à cette réclamation.
                    </p>
                  )}
                </div>
              </div>

              {/* Annonce exacte concernée + compteur de réclamations sur cette annonce */}
              {r.bien_titre && (
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                  <p className="flex items-center gap-1.5 text-sm text-[var(--color-ink-2)]">
                    <Home size={14} className="shrink-0 text-[var(--color-ink-3)]" />
                    Annonce concernée : <span className="font-medium text-[var(--color-ink)]">{r.bien_titre}</span>
                    {r.bien_reclamations_count != null && (
                      <span
                        className={`ml-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                          r.bien_reclamations_count > SEUIL_RECLAMATIONS_ANNONCE
                            ? "bg-[var(--color-rust)]/15 text-[var(--color-rust)]"
                            : "bg-[var(--color-paper-2)] text-[var(--color-ink-3)]"
                        }`}
                      >
                        {r.bien_reclamations_count} réclamation{r.bien_reclamations_count > 1 ? "s" : ""} au total
                      </span>
                    )}
                  </p>

                  {r.bien_reclamations_count != null && r.bien_reclamations_count > SEUIL_RECLAMATIONS_ANNONCE && r.bien_id && (
                    <div className="flex items-center gap-2 rounded-md border border-[var(--color-rust)]/40 bg-[var(--color-rust-bg)] px-3 py-1.5">
                      <TriangleAlert size={14} className="shrink-0 text-[var(--color-rust)]" />
                      <span className="text-xs text-[var(--color-rust)]">
                        Seuil de {SEUIL_RECLAMATIONS_ANNONCE} réclamations dépassé
                      </span>
                      <button
                        disabled={deletingBien === r.bien_id}
                        onClick={() => supprimerAnnonce(r.bien_id as string, r.bien_titre)}
                        className="flex items-center gap-1 rounded-md bg-[var(--color-rust)] px-2.5 py-1 text-xs font-medium text-white hover:opacity-90 disabled:opacity-60"
                      >
                        <Trash2 size={12} />
                        {deletingBien === r.bien_id ? "Suppression…" : "Supprimer l'annonce"}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Message de réclamation */}
              <div className="mt-3 rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] p-3">
                <p className="text-xs font-medium uppercase tracking-wide text-[var(--color-ink-3)]">Message</p>
                <p className="mt-1 whitespace-pre-wrap text-sm text-[var(--color-ink-2)]">{r.description}</p>
              </div>

              {/* Date + actions de traitement */}
              <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
                <p className="flex items-center gap-1 font-mono text-xs text-[var(--color-ink-3)]">
                  <Clock size={12} /> Signalée le {new Date(r.date_creation).toLocaleDateString("fr-MA")}
                </p>

                {!closed && (
                  <div className="flex items-center gap-2">
                    {next && (
                      <button
                        disabled={updating === r.id}
                        onClick={() => changeStatut(r, next)}
                        className="flex items-center gap-1.5 rounded-md bg-[var(--color-brass)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
                      >
                        <CheckCircle2 size={13} />
                        {NEXT_LABEL[next]}
                      </button>
                    )}
                    <button
                      disabled={updating === r.id}
                      onClick={() => changeStatut(r, "rejetee")}
                      className="flex items-center gap-1.5 rounded-md border border-[var(--color-line)] px-3 py-1.5 text-xs font-medium text-[var(--color-ink-2)] hover:border-[var(--color-rust)] hover:text-[var(--color-rust)] disabled:opacity-60"
                    >
                      <XCircle size={13} />
                      Rejeter
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

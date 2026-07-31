import { useEffect, useState } from "react";
import { MessageSquareText } from "lucide-react";
import { api } from "../../lib/api";
import type { Avis, Bien, Contrat } from "../../types";
import StarRating from "../../components/ui/StarRating";

// Un contrat "à évaluer" : terminé, et pour lequel je n'ai pas encore laissé
// d'avis sur ce bien.
interface ContratAEvaluer extends Contrat {
  bien?: Bien;
}

export default function AvisPage() {
  const [avis, setAvis] = useState<Avis[]>([]);
  const [aEvaluer, setAEvaluer] = useState<ContratAEvaluer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Formulaire d'avis ouvert pour un contrat donné (id du contrat), avec sa saisie
  const [formOuvert, setFormOuvert] = useState<string | null>(null);
  const [note, setNote] = useState(0);
  const [commentaire, setCommentaire] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const charger = () => {
    setLoading(true);
    setError(null);
    Promise.all([
      api.get<Avis[]>("/avis/me"),
      api.get<Contrat[]>("/contrats/me"),
    ])
      .then(async ([avisList, contrats]) => {
        setAvis(avisList);

        const biensDejaEvalues = new Set(avisList.map((a) => a.bien_id));
        const contratsTermines = contrats.filter(
          (c) => c.statut === "termine" && !biensDejaEvalues.has(c.bien_id)
        );

        const uniqueBienIds = [...new Set(contratsTermines.map((c) => c.bien_id))];
        const biensList = await Promise.all(
          uniqueBienIds.map((id) => api.get<Bien>(`/biens/${id}`).catch(() => null))
        );
        const biensMap: Record<string, Bien> = {};
        biensList.forEach((b) => {
          if (b) biensMap[b.id] = b;
        });

        setAEvaluer(contratsTermines.map((c) => ({ ...c, bien: biensMap[c.bien_id] })));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(charger, []);

  const ouvrirFormulaire = (contratId: string) => {
    setFormOuvert(contratId);
    setNote(0);
    setCommentaire("");
    setSubmitError(null);
  };

  const soumettreAvis = async (contrat: ContratAEvaluer) => {
    if (note === 0) {
      setSubmitError("Choisis une note avant d'envoyer ton avis.");
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    try {
      await api.post<Avis>("/avis", {
        proprietaire_id: contrat.proprietaire_id,
        bien_id: contrat.bien_id,
        note,
        commentaire: commentaire.trim() || undefined,
      });
      setFormOuvert(null);
      charger(); // recharge la liste (l'avis quitte "à évaluer" et rejoint "mes avis")
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Une erreur est survenue");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Mes avis</h1>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}

      {/* Contrats terminés en attente d'un avis */}
      {!loading && aEvaluer.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-3 font-mono text-xs uppercase tracking-widest text-[var(--color-ink-3)]">
            À évaluer
          </h2>
          <div className="space-y-3">
            {aEvaluer.map((c) => (
              <div key={c.id} className="rounded-lg border border-[var(--color-brass)]/40 bg-[#faf5ee] p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-[var(--color-ink)]">{c.bien?.titre ?? "Bien"}</p>
                    <p className="text-xs text-[var(--color-ink-3)]">{c.bien?.ville}</p>
                  </div>
                  {formOuvert !== c.id && (
                    <button
                      onClick={() => ouvrirFormulaire(c.id)}
                      className="rounded-md bg-[var(--color-brass)] px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)]"
                    >
                      Laisser un avis
                    </button>
                  )}
                </div>

                {formOuvert === c.id && (
                  <div className="mt-4 border-t border-[var(--color-line)] pt-4">
                    <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Note</label>
                    <StarRating value={note} onChange={setNote} size={22} />

                    <label className="mb-1 mt-3 block text-xs font-medium text-[var(--color-ink-2)]">
                      Commentaire (optionnel)
                    </label>
                    <textarea
                      value={commentaire}
                      onChange={(e) => setCommentaire(e.target.value)}
                      rows={3}
                      placeholder="Ton expérience avec ce propriétaire…"
                      className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                    />

                    {submitError && (
                      <p className="mt-2 text-xs text-[var(--color-rust)]">{submitError}</p>
                    )}

                    <div className="mt-3 flex gap-2">
                      <button
                        onClick={() => soumettreAvis(c)}
                        disabled={submitting}
                        className="rounded-md bg-[var(--color-brass)] px-4 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
                      >
                        {submitting ? "Envoi…" : "Envoyer l'avis"}
                      </button>
                      <button
                        onClick={() => setFormOuvert(null)}
                        className="rounded-md px-4 py-1.5 text-xs font-medium text-[var(--color-ink-2)] hover:bg-white"
                      >
                        Annuler
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Avis déjà laissés */}
      <h2 className="mb-3 mt-8 font-mono text-xs uppercase tracking-widest text-[var(--color-ink-3)]">
        Avis laissés
      </h2>
      {!loading && avis.length === 0 && !error && (
        <p className="flex items-center gap-2 text-sm text-[var(--color-ink-3)]">
          <MessageSquareText size={16} />
          Tu n'as encore laissé aucun avis. Un contrat terminé apparaîtra ici pour que tu puisses en
          laisser un.
        </p>
      )}

      <div className="space-y-3">
        {avis.map((a) => (
          <div key={a.id} className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-[var(--color-ink)]">
                {a.bien_titre ?? `Bien réf. ${a.bien_id.slice(0, 8)}`}
              </span>
              <StarRating value={a.note} />
            </div>
            {a.commentaire && <p className="mt-2 text-sm text-[var(--color-ink-2)]">{a.commentaire}</p>}
            <p className="mt-2 font-mono text-xs text-[var(--color-ink-3)]">
              {new Date(a.date_creation).toLocaleDateString("fr-MA")}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

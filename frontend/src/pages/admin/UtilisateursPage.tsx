import { useEffect, useState } from "react";
import { CheckCircle2, Clock, XCircle } from "lucide-react";
import { api } from "../../lib/api";
import type { Utilisateur } from "../../types";

const ROLE_LABEL: Record<string, string> = {
  proprietaire: "Propriétaire",
  client: "Client",
  admin: "Admin",
};

export default function UtilisateursPage() {
  const [utilisateurs, setUtilisateurs] = useState<Utilisateur[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchUsers = () => {
    setLoading(true);
    api
      .get<Utilisateur[]>("/utilisateurs")
      .then(setUtilisateurs)
      .catch((err) => setError(err instanceof Error ? err.message : "Erreur de chargement"))
      .finally(() => setLoading(false));
  };

  useEffect(fetchUsers, []);

  const verifier = async (id: string) => {
    setUpdating(id);
    try {
      await api.patch(`/utilisateurs/${id}/verifier`);
      fetchUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible de vérifier ce compte");
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Utilisateurs</h1>

      {error && (
        <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-4 py-2 text-sm text-[var(--color-rust)]">
          {error}
        </div>
      )}
      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}

      {!loading && (
        <div className="mt-8 overflow-hidden rounded-lg border border-[var(--color-line)] bg-[var(--color-card)]">
          <table className="w-full text-left text-sm">
            <thead className="bg-[var(--color-paper-2)] font-mono text-xs uppercase tracking-wide text-[var(--color-ink-2)]">
              <tr>
                <th className="px-4 py-3">Nom</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Rôle</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {utilisateurs.map((u) => (
                <tr key={u.id} className="border-t border-[var(--color-line)]">
                  <td className="px-4 py-3 font-medium text-[var(--color-ink)]">
                    {u.prenom} {u.nom}
                  </td>
                  <td className="px-4 py-3 text-[var(--color-ink-2)]">{u.email}</td>
                  <td className="px-4 py-3 text-[var(--color-ink-2)]">{ROLE_LABEL[u.role]}</td>
                  <td className="px-4 py-3">
                    {u.statut_verification === "verifie" && (
                      <span className="inline-flex items-center gap-1 text-[var(--color-sage)]">
                        <CheckCircle2 size={15} /> Vérifié
                      </span>
                    )}
                    {u.statut_verification === "en_attente" && (
                      <span className="inline-flex items-center gap-1 text-[var(--color-brass-deep)]">
                        <Clock size={15} /> En attente
                      </span>
                    )}
                    {u.statut_verification === "rejete" && (
                      <span className="inline-flex items-center gap-1 text-[var(--color-rust)]">
                        <XCircle size={15} /> Rejeté
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {u.statut_verification === "en_attente" && (
                      <button
                        disabled={updating === u.id}
                        onClick={() => verifier(u.id)}
                        className="rounded-md bg-[var(--color-brass)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
                      >
                        Vérifier
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

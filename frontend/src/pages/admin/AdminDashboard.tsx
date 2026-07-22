import { useEffect, useState } from "react";
import { Users, ShieldAlert, UserCheck } from "lucide-react";
import StatCard from "../../components/ui/StatCard";
import { api } from "../../lib/api";
import type { Reclamation, Utilisateur } from "../../types";
import StatusBadge from "../../components/ui/StatusBadge";

export default function AdminDashboard() {
  const [utilisateurs, setUtilisateurs] = useState<Utilisateur[]>([]);
  const [reclamations, setReclamations] = useState<Reclamation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<Utilisateur[]>("/utilisateurs"),
      api.get<Reclamation[]>("/reclamations"),
    ])
      .then(([u, r]) => {
        setUtilisateurs(u);
        setReclamations(r);
      })
      .finally(() => setLoading(false));
  }, []);

  const enAttente = utilisateurs.filter((u) => u.statut_verification === "en_attente").length;
  const ouvertes = reclamations.filter((r) => r.statut === "ouverte" || r.statut === "en_cours").length;

  return (
    <div>
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Vue d'ensemble</h1>

      {loading && <p className="mt-6 text-sm text-[var(--color-ink-3)]">Chargement…</p>}

      {!loading && (
        <>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label="Utilisateurs" value={String(utilisateurs.length)} icon={Users} />
            <StatCard
              label="Propriétaires à vérifier"
              value={String(enAttente)}
              icon={UserCheck}
            />
            <StatCard label="Réclamations ouvertes" value={String(ouvertes)} icon={ShieldAlert} />
          </div>

          <h2 className="mt-10 mb-4 font-display text-lg text-[var(--color-ink)]">
            Réclamations récentes
          </h2>
          <div className="space-y-3">
            {reclamations.slice(0, 5).map((r) => (
              <div
                key={r.id}
                className="flex items-center justify-between rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-4"
              >
                <div>
                  <div className="font-medium text-[var(--color-ink)]">{r.type_reclamation}</div>
                  <div className="text-xs text-[var(--color-ink-3)]">{r.description}</div>
                </div>
                <StatusBadge status={r.statut} />
              </div>
            ))}
            {reclamations.length === 0 && (
              <p className="text-sm text-[var(--color-ink-3)]">Aucune réclamation.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}

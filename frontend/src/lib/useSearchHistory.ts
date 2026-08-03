// Historique de recherche (page de recherche client) : charge les
// recherches récentes du client connecté, permet d'en enregistrer une
// nouvelle (avec dédoublonnage/purge gérés côté back-end), d'en supprimer
// une ou de tout effacer.
import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { useAuth } from "./auth";
import type { CriteresRecherche, RechercheHistorique } from "../types";

export function useSearchHistory() {
  const { user } = useAuth();
  const [historique, setHistorique] = useState<RechercheHistorique[]>([]);
  const [loading, setLoading] = useState(true);

  const recharger = useCallback(() => {
    if (!user || user.role !== "client") {
      setHistorique([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    api
      .get<RechercheHistorique[]>("/recherches/me")
      .then(setHistorique)
      .catch(() => setHistorique([])) // best-effort : l'historique n'est jamais bloquant
      .finally(() => setLoading(false));
  }, [user?.id, user?.role]);

  useEffect(recharger, [recharger]);

  // Enregistrement best-effort : n'affecte jamais la recherche en cours
  // même en cas d'échec réseau (l'utilisateur ne voit aucune erreur).
  const enregistrer = async (label: string, criteres: CriteresRecherche) => {
    if (!user || user.role !== "client") return;
    try {
      const nouvelle = await api.post<RechercheHistorique>("/recherches", { label, criteres });
      setHistorique((prev) => [nouvelle, ...prev.filter((r) => r.id !== nouvelle.id)].slice(0, 15));
    } catch {
      // silencieux — voir commentaire ci-dessus
    }
  };

  const supprimer = async (id: string) => {
    setHistorique((prev) => prev.filter((r) => r.id !== id));
    try {
      await api.del(`/recherches/${id}`);
    } catch {
      // best-effort : l'état local reste à jour même si la requête échoue
    }
  };

  const viderTout = async () => {
    setHistorique([]);
    try {
      await api.del("/recherches/me");
    } catch {
      // best-effort
    }
  };

  return { historique, loading, enregistrer, supprimer, viderTout };
}

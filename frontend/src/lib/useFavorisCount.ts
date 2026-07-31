// Compteur d'« Annonces enregistrées » (favoris) affiché dans la nav de
// l'espace client. Se recharge au montage puis à chaque changement signalé
// via favorisEvents (ajout/retrait depuis une fiche bien ou depuis la page
// "Annonces enregistrées" elle-même).
import { useEffect, useState } from "react";
import { api } from "./api";
import { useAuth } from "./auth";
import { subscribeFavorisChanged } from "./favorisEvents";

export function useFavorisCount() {
  const { user } = useAuth();
  const [count, setCount] = useState(0);

  const refresh = () => {
    if (!user || user.role !== "client") return;
    api
      .get<string[]>("/favoris/me/ids")
      .then((ids) => setCount(ids.length))
      .catch(() => {
        /* silencieux — un compteur qui ne se met pas à jour n'est pas bloquant */
      });
  };

  useEffect(() => {
    refresh();
    const unsubscribe = subscribeFavorisChanged(refresh);
    return unsubscribe;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  return count;
}

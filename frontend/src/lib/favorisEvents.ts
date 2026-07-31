// Petit bus d'événements pour synchroniser le compteur de favoris affiché
// dans la nav (DashboardLayout) avec les actions d'ajout/retrait qui ont
// lieu ailleurs (fiche détaillée d'un bien, page "Annonces enregistrées").
// Évite d'avoir à faire remonter un état global juste pour un compteur.
const EVENT_NAME = "smartrent:favoris-changed";

export function emitFavorisChanged() {
  window.dispatchEvent(new Event(EVENT_NAME));
}

export function subscribeFavorisChanged(callback: () => void): () => void {
  window.addEventListener(EVENT_NAME, callback);
  return () => window.removeEventListener(EVENT_NAME, callback);
}

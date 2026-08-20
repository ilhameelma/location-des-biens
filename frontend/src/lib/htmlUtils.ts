/**
 * Dérive un extrait texte brut à partir du contenu HTML d'un article,
 * utilisé quand aucun extrait n'a été saisi manuellement (cartes du blog,
 * aperçu sur la landing page, meta description).
 *
 * Le contenu est déjà sanitizé côté serveur (nh3) avant stockage — cette
 * fonction ne fait que retirer les balises pour l'affichage, ce n'est pas
 * une couche de sécurité supplémentaire.
 */
export function stripHtml(html: string, maxLength = 160): string {
  const texte = html
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (texte.length <= maxLength) return texte;
  return `${texte.slice(0, maxLength).trimEnd()}…`;
}

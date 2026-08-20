import BlogManager from "../../components/blog/BlogManager";

/**
 * Gestion du blog côté admin — voit tous les articles (admin + agences),
 * peut modérer (dépublier/supprimer) n'importe lequel. Logique partagée
 * avec l'espace agence via BlogManager, voir ce composant pour le détail.
 */
export default function ActualitesPage() {
  return <BlogManager />;
}

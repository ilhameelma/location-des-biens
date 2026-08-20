import BlogManager from "../../components/blog/BlogManager";

/**
 * Gestion du blog côté agence — ne voit et ne peut modifier que ses
 * propres articles (filtrage fait côté back, `GET /actualites/admin`).
 * Les articles publiés apparaissent sous le nom de l'agence sur le blog
 * public (voir `auteur_affichage` dans routers/actualites.py).
 */
export default function BlogPage() {
  return <BlogManager />;
}

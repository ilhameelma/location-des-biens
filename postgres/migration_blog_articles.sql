-- ============================================================
-- Migration : upgrade de la table "actualite" en vrai blog
-- ============================================================
-- À appliquer une seule fois sur une base existante (VM) :
--   cat migration_blog_articles.sql | docker exec -i smartrent_postgres psql -U smartrent -d smartrent_db
--
-- Compatible avec un ré-exécution accidentelle (ADD COLUMN IF NOT EXISTS).

ALTER TABLE actualite ADD COLUMN IF NOT EXISTS slug VARCHAR(220);
ALTER TABLE actualite ADD COLUMN IF NOT EXISTS extrait VARCHAR(300);
ALTER TABLE actualite ADD COLUMN IF NOT EXISTS categorie VARCHAR(50) NOT NULL DEFAULT 'actualite';

-- Contrainte de catégorie ajoutée séparément (pas de "ADD CONSTRAINT IF NOT
-- EXISTS" en PostgreSQL) — protégée par un bloc DO pour être rejouable.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'actualite_categorie_check'
    ) THEN
        ALTER TABLE actualite ADD CONSTRAINT actualite_categorie_check
            CHECK (categorie IN (
                'actualite', 'marche_immobilier', 'conseils_locataires',
                'conseils_proprietaires', 'guide_juridique', 'vie_pratique'
            ));
    END IF;
END $$;

-- Renomme la colonne "contenu" en "contenu_html" (contenu riche produit par
-- l'éditeur front, sanitizé côté serveur avant écriture) — sans effet si
-- déjà renommée (ré-exécution).
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'actualite' AND column_name = 'contenu'
    ) THEN
        ALTER TABLE actualite RENAME COLUMN contenu TO contenu_html;
    END IF;
END $$;

-- Slug unique une fois rétro-rempli (le backend le fait à la volée à la
-- première lecture de chaque article existant) ; index créé dès maintenant,
-- NULL autorisé le temps du rétro-remplissage progressif.
CREATE UNIQUE INDEX IF NOT EXISTS idx_actualite_slug ON actualite(slug) WHERE slug IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_actualite_categorie ON actualite(categorie, publie, date_creation DESC);

-- Fin de la migration

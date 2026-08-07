import pandas as pd
import re
import numpy as np

# ============================================
# 1. CHARGEMENT DES DONNÉES
# ============================================
df = pd.read_csv('sarouty_ventes_clean.csv', encoding='utf-8-sig')

print(f"📊 Données chargées : {len(df)} lignes")
print(f"📋 Colonnes : {df.columns.tolist()}")

# ============================================
# 2. SUPPRESSION DES ANONCES DE TEST
# ============================================
test_keywords = ['test', 'annonce test']
df = df[~df['titre'].str.lower().str.contains('|'.join(test_keywords), na=False)]
print(f"✅ Annonces de test supprimées : {len(df)} lignes restantes")

# ============================================
# 3. NETTOYAGE DES PRIX (conversion en numérique)
# ============================================
df['prix_dh'] = pd.to_numeric(df['prix_dh'], errors='coerce')
print(f"💰 Prix convertis en numérique")

# ============================================
# 4. NETTOYAGE DE LA SURFACE
# ============================================
df['surface_m2'] = pd.to_numeric(df['surface_m2'], errors='coerce')

# Extraction de la surface depuis le titre si manquante
def extract_surface_from_title(title):
    if pd.isna(title):
        return np.nan
    match = re.search(r'(\d+)\s*m[²2]', str(title))
    return float(match.group(1)) if match else np.nan

df['surface_from_title'] = df['titre'].apply(extract_surface_from_title)
df['surface_m2'] = df['surface_m2'].fillna(df['surface_from_title'])
df.drop('surface_from_title', axis=1, inplace=True)

# Suppression des surfaces aberrantes (> 1000 m² pour un appartement)
# On garde les villas avec grandes surfaces
df.loc[df['surface_m2'] > 1000, 'surface_m2'] = np.nan
print(f"📐 Surfaces nettoyées")

# ============================================
# 5. NETTOYAGE DU NOMBRE DE CHAMBRES
# ============================================
df['chambres'] = pd.to_numeric(df['chambres'], errors='coerce')

# Extraction des chambres depuis le titre
def extract_chambres_from_title(title):
    if pd.isna(title):
        return np.nan
    patterns = [
        r'(\d+)\s*ch',
        r'(\d+)\s*chambres?',
        r'(\d+)\s*pi[eè]ces?',
        r'(\d+)\s*br'
    ]
    for pattern in patterns:
        match = re.search(pattern, str(title), re.IGNORECASE)
        if match:
            return float(match.group(1))
    return np.nan

df['chambres_from_title'] = df['titre'].apply(extract_chambres_from_title)
df['chambres'] = df['chambres'].fillna(df['chambres_from_title'])
df.drop('chambres_from_title', axis=1, inplace=True)

# Correction des incohérences flagrantes
df.loc[df['chambres'] == 0, 'chambres'] = np.nan
print(f"🛏️ Chambres nettoyées")

# ============================================
# 6. NETTOYAGE DES SALLES DE BAIN
# ============================================
df['salles_de_bain'] = pd.to_numeric(df['salles_de_bain'], errors='coerce')

# Si le titre mentionne "salle de bain", on extrait
def extract_bathrooms_from_title(title):
    if pd.isna(title):
        return np.nan
    match = re.search(r'(\d+)\s*salles? de bain', str(title), re.IGNORECASE)
    if match:
        return float(match.group(1))
    return np.nan

df['sdb_from_title'] = df['titre'].apply(extract_bathrooms_from_title)
df['salles_de_bain'] = df['salles_de_bain'].fillna(df['sdb_from_title'])
df.drop('sdb_from_title', axis=1, inplace=True)

# Si une salle de bain manque mais qu'il y a des chambres, on estime
# Règle : 1 salle de bain pour 2 chambres (minimum 1)
def estimate_bathrooms(row):
    if pd.isna(row['salles_de_bain']) and not pd.isna(row['chambres']):
        return max(1, int(np.ceil(row['chambres'] / 2)))
    return row['salles_de_bain']

df['salles_de_bain'] = df.apply(estimate_bathrooms, axis=1)
print(f"🚿 Salles de bain nettoyées")

# ============================================
# 7. STANDARDISATION DES QUARTIERS
# ============================================
quartier_mapping = {
    # Casablanca
    'Dar Bouazza': ['Dar Bouazza', 'Darbouazza', 'Dar Bouaaza', 'Dar-bouazza', 'Dar Bouaza'],
    'Anfa': ['Anfa', 'Bd Anfa', 'Boulevard Anfa', 'Casa Anfa'],
    'Racine': ['Racine'],
    'Maarif': ['Maarif', 'Maarif Extension', 'Maârif', 'Maarif ', 'Maarif Extension'],
    'Gauthier': ['Gauthier', 'Gauhtier'],
    'Sidi Belyout': ['Sidi Belyout', 'Bourgogne', 'Bourgone'],
    'Hay Riad': ['Hay Riad', 'Prestigia', 'Haut Agdal', 'Quartier Agdal Haut', 'Agdal'],
    'Palmeraie': ['Palmeraie'],
    'Guéliz': ['Guéliz', 'Gueliz'],
    'Hivernage': ['Hivernage'],
    'Les Princesses': ['Les Princesses'],
    'Sidi rahal': ['Sidi rahal', 'Sidi Rahal'],
    'Tamaris': ['Tamaris'],
    'Zenata': ['Zenata'],
    'Bouskoura': ['Bouskoura'],
    'Ain Diab': ['Ain Diab', 'Aïn Diab'],
    'Souissi': ['Souissi', 'Souissi'],
    'Plage des Nations': ['Plage des Nations', 'Plage des nations'],
    'Val Fleuri': ['Val Fleuri', 'Val Fleury', 'Valfleury'],
    'Mohammedia': ['Mohammedia', 'Bouznika'],
    'Oasis': ['Oasis'],
    'Palmier': ['Palmier'],
    'Californie': ['Californie'],
    'Ain Chock': ['Ain Chock', 'AIN CHOCK'],
    'Hay Hassani': ['Hay Hassani', 'CIL'],
    'Mabella': ['Mabella'],
    '2 Mars': ['2 Mars'],
    'Socrate': ['Socrate'],
    'Guich oudayas': ['Guich oudayas', 'Oulad Mtae'],
    'Chrifia': ['Chrifia', 'Noria'],
    'Agdal': ['Agdal', 'Quartier Agdal Bas', 'Bas Agdal'],
    'Al izdihar': ['Al izdihar', 'Izdihar', 'Hay Izdihar', 'Al Izdihar'],
    'Hay Charaf': ['Hay Charaf', 'Charaf'],
    'Allal El Fassi': ['Allal El Fassi', 'Allal Al Fassi'],
    'Semlalia': ['Semlalia'],
    'Majorelle': ['Majorelle'],
    'Route de Casablanca': ['Route de Casablanca', 'Route de Casa'],
    'Menara': ['Menara'],
    'Malabata': ['Malabata'],
    'Mesnana': ['Mesnana'],
    'Mhamid': ['Mhamid'],
    'Tamansourt': ['Tamansourt', 'Tamensourt'],
    'Azzouzia': ['Azzouzia'],
    'Oulfa': ['Oulfa'],
    'Nassim': ['Nassim'],
    'Mers Sultan': ['Mers Sultan', 'Habous'],
    'Derb Sultan': ['Derb Sultan'],
    'Sidi Moumen': ['Sidi Moumen'],
    'Roches Noires': ['Roches Noires'],
    'Benslimane': ['Benslimane'],
    'Fès': ['Fès'],
    'Meknès': ['Meknès'],
    'Agadir': ['Agadir'],
    'El Jadida': ['El-Jadida', 'El Jadida'],
    'Saïdia': ['saidia'],
    'Safi': ['Route de Safi'],
    'Tamesna': ['Tamesna'],
    'Bouznika Bay': ['Bouznika Bay'],
    'Marrakech Golf City': ['Marrakech Golf City'],
    'Casa Green Town': ['Casa Green Town', 'La Ville Verte'],
    'Marina Casablanca': ['Marina Casablanca', 'Casa Marina'],
    'La Marina Salé': ['La Marina Salé', 'Salé Marina'],
    'Bab al bahr': ['Bab al bahr'],
    'Annakhil': ['Annakhil'],
    'Mabrouka': ['Mabrouka'],
    'Sidi Maarouf': ['Sidi Maarouf'],
    'Ferme Bretone': ['Ferme Bretone', 'Ferme Bretonne'],
    'Alsace Lorraine': ['Alsace Lorraine'],
    'El Menzeh': ['El menzeh', 'El Menzeh'],
    'Quartier des Hôpitaux': ['Quartier des Hôpitaux', 'Hopitaux', 'Hôpitaux'],
    'Triangle d\'Or': ['Triangle d\'Or', 'Triangle D\'or', 'Triangle d\'or'],
    'Océan': ['L\'Ocean', 'Océan'],
    'Saada': ['Saada', 'Diour Marjane'],
    'Targa': ['Targa'],
    'Riviera': ['Riviera'],
    'Boulevard Ghandi': ['Boulevard Ghandi', 'Ghandi'],
    'Errahma': ['Errahma'],
    'Nouaceur': ['Nouaceur', 'Nouacer'],
    'Berrechid': ['Berrechid'],
    'Ain Borja': ['Ain Borja'],
    'Beauséjour': ['Beauséjour'],
    'Benjdia': ['Benjdia'],
    'Derb Ghallef': ['Derb Ghallef'],
    'Hay Mohammadi': ['Hay Mohammadi'],
    'Lissasfa': ['Lissasfa'],
    'Mandarina': ['Mandarona', 'Mandarina'],
    'Route Amizmiz': ['Route Amizmiz'],
    'Route de Fès': ['Route de Fès', 'Fassi'],
    'Route de Ouarzazate': ['Route de Ouarzazate'],
    'Route de Tahanaoute': ['Route de Tahanaoute'],
    'Route de Tamansourt': ['Route de Tamansourt'],
    'Sable d\'Or': ['Sable d\'Or'],
    'Victor Hugo': ['Victor Hugo', 'Camp El Ghoul'],
    'Yacoub El Mansour': ['Yacoub El Mansour', 'Avenue Yacoub El Mansour'],
    'Zerktouni': ['Zerktouni'],
    'Avenue Mohammed VI': ['Avenue Mohammed VI', 'Bv M6'],
    'Abdelmoumen': ['Abdelmoumen', 'Bd Abdelmoumen'],
    'Av Abdelkrim El Khattabi': ['Av Abdelkrim El Khattabi', 'Boulevard Abdelkrim Khettabi'],
    'Boulevard Al Massira Al Khadra': ['Boulevard Al Massira Al Khadra', 'Al Massira', 'Massira'],
    'Daoudiate': ['Daoudiate'],
    'Ibn tachfine': ['Ibn tachfine'],
    'Kebibat': ['Kebibat'],
    'Marjane': ['Marjane'],
    'Plage': ['Plage'],
    'Wafa': ['Wafa'],
    'Wifak': ['Wifak'],
    'Autre': ['Autre', 'indéfini', 'Médina', 'Centre ville', 'Centre Ville Casablanca', 'Casablanca', 'Marrakech', 'Rabat', 'Tanger', 'Autre'],
}

# Application du mapping
def standardize_quartier(q):
    if pd.isna(q):
        return 'Autre'
    q = str(q).strip()
    for standard, variations in quartier_mapping.items():
        if q in variations or q == standard:
            return standard
    # Si le quartier contient un nom connu
    for standard, variations in quartier_mapping.items():
        for var in variations:
            if var.lower() in q.lower() or q.lower() in var.lower():
                return standard
    return 'Autre'

df['quartier'] = df['quartier'].apply(standardize_quartier)
print(f"🏘️ Quartiers standardisés : {df['quartier'].nunique()} quartiers uniques")

# ============================================
# 8. DÉTECTION DU TYPE DE BIEN
# ============================================
def detect_property_type(title):
    if pd.isna(title):
        return 'Appartement'
    title_lower = str(title).lower()
    if 'villa' in title_lower:
        return 'Villa'
    elif 'studio' in title_lower:
        return 'Studio'
    elif 'duplex' in title_lower:
        return 'Duplex'
    elif 'penthouse' in title_lower:
        return 'Penthouse'
    elif 'rez-de-jardin' in title_lower or 'rdj' in title_lower:
        return 'Rez-de-jardin'
    else:
        return 'Appartement'

df['type_bien'] = df['titre'].apply(detect_property_type)
print(f"🏠 Types de biens détectés : {df['type_bien'].unique().tolist()}")

# ============================================
# 9. EXTRACTION DU PRIX AU M²
# ============================================
df['prix_m2'] = df['prix_dh'] / df['surface_m2']
print(f"📊 Prix au m² calculé")

# ============================================
# 10. SUPPRESSION DES LIGNES AVEC PRIX MANQUANT
# ============================================
df = df.dropna(subset=['prix_dh'])
print(f"💰 Lignes avec prix conservées : {len(df)}")

# ============================================
# 11. RÉORGANISATION DES COLONNES
# ============================================
columns_order = [
    'source', 'listing_id', 'titre', 'type_bien', 'quartier',
    'prix_dh', 'surface_m2', 'prix_m2',
    'chambres', 'salles_de_bain'
]
df = df[columns_order]

# ============================================
# 12. SAUVEGARDE DES DONNÉES NETTOYÉES
# ============================================
df.to_csv('sarouty_ventes_clean_final.csv', index=False, encoding='utf-8-sig')
print(f"\n✅ DONNÉES NETTOYÉES SAUVEGARDÉES !")
print(f"📊 {len(df)} lignes")
print(f"📋 Colonnes : {df.columns.tolist()}")
print(f"\n📈 Statistiques rapides :")
print(df.describe())

# ============================================
# 13. RAPPORT DE NETTOYAGE
# ============================================
print("\n" + "="*50)
print("📊 RAPPORT DE NETTOYAGE")
print("="*50)
print(f"🏘️ Quartiers uniques : {df['quartier'].nunique()}")
print(f"🏠 Types de biens : {df['type_bien'].nunique()}")
print(f"💰 Prix moyen : {df['prix_dh'].mean():,.0f} DH")
print(f"📐 Surface moyenne : {df['surface_m2'].mean():.1f} m²")
print(f"📊 Prix moyen au m² : {df['prix_m2'].mean():.0f} DH/m²")
print(f"🛏️ Chambres moyennes : {df['chambres'].mean():.1f}")
print(f"🚿 Salles de bain moyennes : {df['salles_de_bain'].mean():.1f}")
print("="*50)
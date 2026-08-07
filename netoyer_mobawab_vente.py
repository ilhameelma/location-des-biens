import pandas as pd
import re
import numpy as np

# ============================================
# 1. CHARGEMENT
# ============================================
df = pd.read_csv('mubawab_ventes.csv', encoding='utf-8-sig')

print(f"📊 Données chargées : {len(df)} lignes")

# ============================================
# 2. NETTOYAGE DES PRIX
# ============================================
df['prix_dh'] = pd.to_numeric(df['prix_dh'], errors='coerce')
print(f"💰 Prix : {df['prix_dh'].notna().sum()} valeurs valides")

# ============================================
# 3. EXTRACTION DES DONNEES DEPUIS LA DESCRIPTION
# ============================================
def extract_surface(desc):
    if pd.isna(desc):
        return np.nan
    match = re.search(r'(\d+)\s*m[²2]', str(desc))
    return float(match.group(1)) if match else np.nan

def extract_chambres(desc):
    if pd.isna(desc):
        return np.nan
    match = re.search(r'(\d+)\s*chambres?', str(desc), re.IGNORECASE)
    return float(match.group(1)) if match else np.nan

def extract_sdb(desc):
    if pd.isna(desc):
        return np.nan
    match = re.search(r'(\d+)\s*salles? de bain', str(desc), re.IGNORECASE)
    return float(match.group(1)) if match else np.nan

def extract_pieces(desc):
    if pd.isna(desc):
        return np.nan
    match = re.search(r'(\d+)\s*pi[eè]ces?', str(desc), re.IGNORECASE)
    return float(match.group(1)) if match else np.nan

# Application
df['surface_from_desc'] = df['description'].apply(extract_surface)
df['chambres_from_desc'] = df['description'].apply(extract_chambres)
df['sdb_from_desc'] = df['description'].apply(extract_sdb)
df['pieces_from_desc'] = df['description'].apply(extract_pieces)

# Remplissage des colonnes vides
df['surface_m2'] = df['surface_m2'].fillna(df['surface_from_desc'])
df['chambres'] = df['chambres'].fillna(df['chambres_from_desc'])
df['salles_de_bain'] = df['salles_de_bain'].fillna(df['sdb_from_desc'])
df['pieces'] = df['pieces'].fillna(df['pieces_from_desc'])

print(f"📐 Surface extraite : {df['surface_m2'].notna().sum()} valeurs")
print(f"🛏️ Chambres extraites : {df['chambres'].notna().sum()} valeurs")

# ============================================
# 4. DETECTION DU TYPE DE BIEN
# ============================================
def detect_type(title):
    if pd.isna(title):
        return 'Appartement'
    t = str(title).lower()
    if 'villa' in t:
        return 'Villa'
    elif 'studio' in t:
        return 'Studio'
    elif 'duplex' in t:
        return 'Duplex'
    elif 'penthouse' in t:
        return 'Penthouse'
    else:
        return 'Appartement'

df['type_bien'] = df['titre'].apply(detect_type)

# ============================================
# 5. DETECTION DES PROJETS
# ============================================
def is_project(title):
    keywords = ['projet', 'résidence', 'programme', 'nouveau projet', 'projet immobilier', 
                'livraison', 'sur plan', 'en cours de construction', 'promoteur']
    t = str(title).lower()
    return any(kw in t for kw in keywords)

df['is_project'] = df['titre'].apply(is_project)

# ============================================
# 6. SUPPRESSION DES DOUBLONS
# ============================================
df = df.drop_duplicates(subset=['url'])
print(f"🗑️ Doublons supprimés : {len(df)} lignes uniques")

# ============================================
# 7. SUPPRESSION DES ANONCES TEST
# ============================================
df = df[~df['titre'].str.lower().str.contains('test', na=False)]

# ============================================
# 8. SUPPRESSION DES LIGNES SANS PRIX
# ============================================
df = df.dropna(subset=['prix_dh'])

# ============================================
# 9. SAUVEGARDE
# ============================================
df.to_csv('mubawab_ventes_clean.csv', index=False, encoding='utf-8-sig')

print(f"\n✅ DONNÉES NETTOYÉES : {len(df)} lignes")
print(f"📊 Prix moyen : {df['prix_dh'].mean():,.0f} DH")
print(f"📐 Surface moyenne : {df['surface_m2'].mean():.1f} m²")
print(f"🏠 Types : {df['type_bien'].value_counts().to_dict()}")
print(f"📋 Projets : {df['is_project'].value_counts().to_dict()}")
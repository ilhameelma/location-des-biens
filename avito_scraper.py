import requests
from bs4 import BeautifulSoup
import csv
import re
import json
import time

# Votre clé API
API_KEY = "4TDDRCVNRKZSVD3NW3RSJLY5EBR7IN1MTHD7TER1MXO41EHB1UHFA2SMKLQTACFKDE48TVZ0HIN6LCRR"

def scraper_avec_scrapingbee(url):
    """Scrape via ScrapingBee avec paramètres VALIDES"""
    
    # Paramètres supportés par ScrapingBee
    params = {
        'api_key': API_KEY,
        'url': url,
        'render_js': 'true',
        'premium_proxy': 'true',
        'country_code': 'fr',
        'wait_for': '.property-item, .listing-item, article',  # Sélecteur CSS valide
    }
    
    print(f"⏳ Envoi de la requête à ScrapingBee...")
    
    try:
        response = requests.get(
            'https://app.scrapingbee.com/api/v1/',
            params=params,
            timeout=60
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Page récupérée avec succès !")
            return BeautifulSoup(response.text, 'html.parser')
        else:
            print(f"❌ Erreur ScrapingBee: {response.status_code}")
            print(f"   Réponse: {response.text[:300]}")
            
            # Suggestions pour l'erreur
            if "wait_for" in response.text:
                print("\n💡 Le sélecteur CSS n'est pas trouvé. Essayez 'body' ou 'div'")
            return None
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None

def extraire_annonces(soup):
    """Extrait les annonces du HTML"""
    if not soup:
        return []
    
    annonces = []
    
    # 1. Chercher dans les scripts JavaScript (méthode la plus fiable)
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            # Chercher les IDs des propriétés
            ids = re.findall(r'property_id["\']?\s*:\s*(\d+)', script.string)
            if ids:
                print(f"🔍 IDs trouvés: {ids[:5]}")
                for pid in set(ids[:10]):
                    try:
                        pattern = rf'property_id["\']?\s*:\s*{pid}[^}}]*}}'
                        matches = re.findall(pattern, script.string)
                        for match in matches:
                            data_str = match.replace('\\', '').strip()
                            if data_str.startswith('{'):
                                try:
                                    data = json.loads(data_str)
                                    annonce = {
                                        'id': pid,
                                        'titre': data.get('title', data.get('titre', 'N/A')),
                                        'prix': data.get('price', data.get('prix', 'N/A')),
                                        'localisation': data.get('location', data.get('localisation', 'N/A')),
                                        'surface': data.get('surface', 'N/A'),
                                        'chambres': data.get('bedrooms', data.get('chambres', 'N/A'))
                                    }
                                    if annonce['titre'] != 'N/A' or annonce['prix'] != 'N/A':
                                        annonces.append(annonce)
                                except:
                                    pass
                    except:
                        pass
    
    # 2. Chercher dans le HTML structuré (méthode de secours)
    if not annonces:
        print("🔍 Recherche dans le HTML structuré...")
        
        # Chercher tous les conteneurs possibles
        for class_pattern in ['property', 'listing', 'item', 'card', 'annonce', 'result']:
            conteneurs = soup.find_all(['div', 'article', 'li'], class_=re.compile(class_pattern, re.I))
            if conteneurs:
                print(f"   {len(conteneurs)} conteneurs trouvés avec '{class_pattern}'")
                break
        
        conteneurs = soup.find_all(['div', 'article'], class_=re.compile(r'(property|listing|item|card)', re.I))
        
        for conteneur in conteneurs:
            texte = conteneur.text
            if ('DH' in texte or 'MAD' in texte) and 'm²' in texte:
                titre_elem = conteneur.find(['h3', 'h2', 'h1'])
                titre = ' '.join(titre_elem.text.strip().split()) if titre_elem else 'N/A'
                
                prix_match = re.search(r'([\d\s,]+)\s*(DH|MAD)', texte)
                prix = prix_match.group(0).strip() if prix_match else 'N/A'
                
                surface_match = re.search(r'(\d+)\s*m²', texte)
                surface = f"{surface_match.group(1)} m²" if surface_match else 'N/A'
                
                if titre != 'N/A' or prix != 'N/A':
                    annonces.append({
                        'id': 'N/A',
                        'titre': titre,
                        'prix': prix,
                        'localisation': 'N/A',
                        'surface': surface,
                        'chambres': 'N/A'
                    })
    
    # Supprimer les doublons
    annonces_uniques = []
    titres_vus = set()
    for annonce in annonces:
        if annonce['titre'] not in titres_vus and annonce['titre'] != 'N/A':
            titres_vus.add(annonce['titre'])
            annonces_uniques.append(annonce)
    
    return annonces_uniques

# === VERSION SIMPLIFIÉE POUR TEST ===
def test_scrapingbee():
    """Test simple pour vérifier que ScrapingBee fonctionne"""
    
    # Tester avec une URL simple
    test_url = "https://example.com"
    print(f"🔍 Test avec {test_url}")
    
    params = {
        'api_key': API_KEY,
        'url': test_url,
    }
    
    try:
        response = requests.get('https://app.scrapingbee.com/api/v1/', params=params, timeout=30)
        print(f"📡 Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ ScrapingBee fonctionne !")
            return True
        else:
            print(f"❌ Échec: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

# === EXÉCUTION PRINCIPALE ===
if __name__ == "__main__":
    print("🔍 Scraping avec ScrapingBee (VERSION ULTIME)")
    print("   Clé API: " + API_KEY[:10] + "...\n")
    
    # 1. Tester si la clé fonctionne
    if not test_scrapingbee():
        print("\n❌ La clé API ne fonctionne pas.")
        print("   Vérifiez sur https://app.scrapingbee.com/dashboard")
        exit()
    
    # 2. Scraper la page Sarouty
    print("\n" + "="*60)
    url = "https://www.sarouty.ma/fr/acheter/"
    print(f"🔍 Scraping de: {url}")
    
    soup = scraper_avec_scrapingbee(url)
    
    if soup:
        annonces = extraire_annonces(soup)
        print(f"\n📊 {len(annonces)} annonces trouvées")
        
        if annonces:
            # Afficher les 5 premières
            for i, annonce in enumerate(annonces[:5], 1):
                print(f"\n🏠 Annonce {i}:")
                for key, value in annonce.items():
                    print(f"   {key.capitalize()}: {value}")
            
            # Sauvegarder en CSV
            with open('annonces_scrapingbee.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'titre', 'prix', 'localisation', 'surface', 'chambres'])
                writer.writeheader()
                writer.writerows(annonces)
            print(f"\n✅ {len(annonces)} annonces exportées dans 'annonces_scrapingbee.csv'")
        else:
            print("\n⚠️ Aucune annonce trouvée")
            print("   Sauvegarde du HTML pour analyse...")
            
            # Sauvegarder le HTML complet
            with open('page_scrapingbee_debug.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print("💾 HTML sauvegardé dans 'page_scrapingbee_debug.html'")
            
            # Afficher les premiers éléments du HTML
            print("\n🔍 Extrait du HTML récupéré:")
            text = str(soup)[:500]
            print(text)
    else:
        print("\n❌ Échec du scraping avec ScrapingBee")
        print("   Causes possibles:")
        print("   1. Le site bloque ScrapingBee")
        print("   2. Problème de réseau")
        print("   3. Paramètres invalides")
        
        print("\n💡 Solution alternative:")
        print("   Utilisez la méthode manuelle dans le navigateur:")
        print("   1. Allez sur https://www.sarouty.ma/fr/acheter/")
        print("   2. F12 → Console")
        print("   3. Collez le script JavaScript d'extraction")
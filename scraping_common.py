"""
scraping_common.py — Brique commune de "scraping poli", partagée entre
avito_scraper.py et sarouty_scraper.py.
 
Respecte :
  - robots.txt (lu et appliqué à CHAQUE requête, via urllib.robotparser)
  - le Crawl-delay annoncé par le site, sinon un délai minimum configurable
  - un arrêt propre en cas de blocage (429, erreurs serveur répétées)
 
⚠️ Rappel : le respect du robots.txt et d'un throttling raisonnable ne
rend pas automatiquement un scraping conforme aux CGU d'un site. Vérifie
toujours manuellement les conditions d'utilisation du site visé.
"""
from __future__ import annotations
 
import random
import sys
import time
import urllib.robotparser
from urllib.parse import urljoin
 
import requests
 
 
class PoliteFetcher:
    """Encapsule le respect du robots.txt + le throttling entre requêtes."""
 
    def __init__(self, base_url: str, user_agent: str, min_delay: float):
        self.base_url = base_url
        self.user_agent = user_agent
        self.min_delay = min_delay
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent, "Accept-Language": "fr-FR,fr"})
 
        self.robots = urllib.robotparser.RobotFileParser()
        self.robots.set_url(urljoin(base_url, "/robots.txt"))
        try:
            self.robots.read()
        except Exception as exc:
            print(f"⚠️  Impossible de lire robots.txt ({exc}) — arrêt par précaution.", file=sys.stderr)
            sys.exit(1)
 
        crawl_delay = self.robots.crawl_delay(user_agent) or self.robots.crawl_delay("*")
        if crawl_delay:
            self.min_delay = max(self.min_delay, float(crawl_delay))
 
        self._last_request = 0.0
 
    def allowed(self, url: str) -> bool:
        return self.robots.can_fetch(self.user_agent, url)
 
    def get(self, url: str) -> requests.Response | None:
        if not self.allowed(url):
            print(f"⛔ robots.txt interdit l'accès à {url} — ignoré.", file=sys.stderr)
            return None
 
        elapsed = time.monotonic() - self._last_request
        wait = self.min_delay - elapsed + random.uniform(0.2, 0.8)
        if wait > 0:
            time.sleep(wait)
 
        try:
            resp = self.session.get(url, timeout=15)
        except requests.RequestException as exc:
            print(f"⚠️  Erreur réseau sur {url} : {exc}", file=sys.stderr)
            return None
        finally:
            self._last_request = time.monotonic()
 
        if resp.status_code == 429:
            print(f"⛔ 429 Too Many Requests sur {url} — arrêt (le site nous throttle).", file=sys.stderr)
            return None
        if resp.status_code >= 400:
            print(f"⚠️  {resp.status_code} sur {url}", file=sys.stderr)
            return None
        return resp
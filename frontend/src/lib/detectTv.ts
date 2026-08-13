/**
 * Détecte si l'application tourne dans le navigateur intégré d'une Smart TV
 * (et non un simple grand écran de bureau — une largeur de fenêtre de
 * 1920px ne suffit pas à distinguer les deux, beaucoup de moniteurs de
 * bureau classiques font aussi cette largeur).
 *
 * Approche : reconnaissance de user-agent des principaux navigateurs
 * embarqués dans les téléviseurs connectés (LG webOS, Samsung Tizen,
 * Android TV / Google TV, Amazon Fire TV, Sony BRAVIA, Hisense/Toshiba
 * VIDAA, HbbTV européen, Opera TV, etc.) — liste large mais standard,
 * volontairement tolérante (mieux vaut rater un modèle obscur que déclencher
 * le mode TV sur un ordinateur de bureau).
 *
 * Override manuel pour les tests/démonstrations sans télé physique :
 *   ?tv=1  → force le mode TV, quel que soit le user-agent
 *   ?tv=0  → force la désactivation du mode TV
 *
 * Persistance (sessionStorage) : comme l'application est une SPA (React
 * Router), la classe posée sur <html> survit déjà naturellement à une
 * navigation interne (pas de rechargement de page). Le seul cas où elle se
 * perdrait est un VRAI rechargement de page ou un nouvel onglet — ex. on
 * teste avec "?tv=1" sur la page d'accueil, puis on tape directement
 * "/client" dans la barre d'adresse, ou on appuie sur F5. Dans ce cas, le
 * choix fait via "?tv=1"/"?tv=0" est mémorisé pour le reste de la session
 * de navigation (onglet), sans avoir à rajouter le paramètre à chaque URL.
 * Le user-agent réel d'une vraie Smart TV, lui, sera de toute façon détecté
 * à nouveau correctement à chaque chargement — cette mémorisation ne sert
 * qu'aux tests manuels via "?tv=".
 */

const TV_USER_AGENT_PATTERN =
  /SmartTV|SMART-TV|GoogleTV|Android TV|AppleTV|HbbTV|NetCast|Tizen|Web0S|WebOS|BRAVIA|AFTT|AFTB|AFTM|AFTS|AFTA|AFTN|VIDAA|CrKey|POV_TV|Espial|OPERATV|OperaTV|ADT-1|BOXEE|DLNADOC|INETTVBROWSER|Kylo|Roku|ViziO/i;

const STORAGE_KEY = "smartrent_tv_mode";

function lireStorage(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    // sessionStorage indisponible (navigation privée stricte, etc.) — pas bloquant
    return null;
  }
}

function ecrireStorage(valeur: "1" | "0"): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, valeur);
  } catch {
    // idem — on continue sans mémorisation plutôt que de faire planter l'app
  }
}

export function detecterEtAppliquerModeTv(): boolean {
  const params = new URLSearchParams(window.location.search);
  const forceParam = params.get("tv");

  let estTv: boolean;

  if (forceParam === "1" || forceParam === "0") {
    // Choix explicite dans l'URL : applique ET mémorise pour le reste de
    // l'onglet, pour ne pas avoir à répéter "?tv=1" sur chaque page.
    estTv = forceParam === "1";
    ecrireStorage(estTv ? "1" : "0");
  } else {
    const stocke = lireStorage();
    if (stocke === "1" || stocke === "0") {
      estTv = stocke === "1";
    } else {
      estTv = TV_USER_AGENT_PATTERN.test(navigator.userAgent || "");
    }
  }

  document.documentElement.classList.toggle("is-tv", estTv);
  return estTv;
}

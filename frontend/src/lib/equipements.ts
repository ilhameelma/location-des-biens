// Catalogue des équipements/commodités proposés par une annonce, façon
// "Ce que propose ce logement" chez Airbnb — voir README_AMELIORATIONS_UI_VENTE_LOCATION.md
// pour le contexte général du projet.
//
// Le catalogue change selon `type_bien` : un logement résidentiel n'a pas
// les mêmes commodités pertinentes qu'un bureau, un magasin, un garage ou
// un terrain. Les codes sont stables (utilisés tels quels en base, colonne
// `bien.equipements`, JSONB) — ne jamais renommer un code existant, au
// besoin en ajouter un nouveau et laisser l'ancien inutilisé.

import type { ComponentType } from "react";
import {
  Wifi,
  Snowflake,
  Flame,
  Camera,
  ShieldCheck,
  ArrowUpDown,
  Zap,
  Armchair,
  ChefHat,
  Tv,
  WashingMachine,
  Wind,
  Refrigerator,
  Sun,
  Trees,
  Waves,
  BellRing,
  Droplet,
  Briefcase,
  Users,
  DoorOpen,
  Lock,
  Utensils,
  Bath,
  Accessibility,
  Store,
  Package,
  Route,
  ParkingSquare,
  Tag,
  Truck,
  Car,
  Ruler,
  Wrench,
  Fence,
  FileCheck,
  Map,
  Mountain,
} from "lucide-react";
import type { TypeBien } from "../types";

export interface Equipement {
  code: string;
  label: string;
  icon: ComponentType<{ size?: number | string; className?: string }>;
}

// ---------- Résidentiel (appartement / maison / villa) ----------
const RESIDENTIEL: Equipement[] = [
  { code: "meuble", label: "Meublé", icon: Armchair },
  { code: "wifi", label: "Wifi", icon: Wifi },
  { code: "cuisine_equipee", label: "Cuisine équipée", icon: ChefHat },
  { code: "climatisation", label: "Climatisation", icon: Snowflake },
  { code: "chauffage", label: "Chauffage", icon: Flame },
  { code: "television", label: "Télévision", icon: Tv },
  { code: "lave_linge", label: "Lave-linge", icon: WashingMachine },
  { code: "seche_linge", label: "Sèche-linge", icon: Wind },
  { code: "refrigerateur", label: "Réfrigérateur", icon: Refrigerator },
  { code: "ascenseur", label: "Ascenseur", icon: ArrowUpDown },
  { code: "parking", label: "Parking / stationnement", icon: ParkingSquare },
  { code: "balcon_terrasse", label: "Balcon / terrasse", icon: Sun },
  { code: "jardin", label: "Jardin", icon: Trees },
  { code: "piscine", label: "Piscine", icon: Waves },
  { code: "chauffe_eau", label: "Chauffe-eau", icon: Droplet },
  { code: "interphone_digicode", label: "Interphone / digicode", icon: BellRing },
  { code: "cameras_surveillance", label: "Caméras de surveillance extérieures", icon: Camera },
  { code: "gardiennage", label: "Gardiennage / sécurité", icon: ShieldCheck },
  { code: "espace_travail", label: "Espace de travail dédié", icon: Briefcase },
];

// ---------- Bureau ----------
const BUREAU: Equipement[] = [
  { code: "meuble_bureau", label: "Mobilier de bureau / postes de travail", icon: Armchair },
  { code: "internet_haut_debit", label: "Internet fibre / haut débit", icon: Wifi },
  { code: "climatisation", label: "Climatisation", icon: Snowflake },
  { code: "chauffage", label: "Chauffage", icon: Flame },
  { code: "ascenseur", label: "Ascenseur", icon: ArrowUpDown },
  { code: "parking", label: "Parking", icon: ParkingSquare },
  { code: "salle_reunion", label: "Salle de réunion", icon: Users },
  { code: "reception_accueil", label: "Réception / accueil", icon: DoorOpen },
  { code: "badge_acces", label: "Contrôle d'accès / badge", icon: Lock },
  { code: "kitchenette", label: "Cuisine / kitchenette", icon: Utensils },
  { code: "sanitaires_prives", label: "Sanitaires privés", icon: Bath },
  { code: "accessible_pmr", label: "Accessible PMR", icon: Accessibility },
  { code: "cameras_surveillance", label: "Caméras de surveillance", icon: Camera },
  { code: "gardiennage", label: "Gardiennage / sécurité", icon: ShieldCheck },
];

// ---------- Magasin (local commercial) ----------
const MAGASIN: Equipement[] = [
  { code: "vitrine_rue", label: "Vitrine sur rue", icon: Store },
  { code: "rideau_metallique", label: "Rideau métallique", icon: Lock },
  { code: "enseigne_autorisee", label: "Pose d'enseigne autorisée", icon: Tag },
  { code: "climatisation", label: "Climatisation", icon: Snowflake },
  { code: "sanitaires", label: "Sanitaires", icon: Bath },
  { code: "reserve_arriere_boutique", label: "Réserve / arrière-boutique", icon: Package },
  { code: "electricite_triphasee", label: "Électricité triphasée", icon: Zap },
  { code: "acces_livraison", label: "Accès livraison", icon: Truck },
  { code: "parking_clients", label: "Parking clients", icon: ParkingSquare },
  { code: "monte_charge", label: "Ascenseur / monte-charge", icon: ArrowUpDown },
  { code: "cameras_surveillance", label: "Caméras de surveillance", icon: Camera },
  { code: "gardiennage", label: "Gardiennage / sécurité", icon: ShieldCheck },
];

// ---------- Garage ----------
const GARAGE: Equipement[] = [
  { code: "porte_motorisee", label: "Porte automatique / motorisée", icon: DoorOpen },
  { code: "eclairage", label: "Éclairage", icon: Sun },
  { code: "electricite", label: "Électricité (prise disponible)", icon: Zap },
  { code: "point_eau", label: "Point d'eau", icon: Droplet },
  { code: "hauteur_adaptee", label: "Hauteur sous plafond adaptée", icon: Ruler },
  { code: "acces_vehicule_facile", label: "Accès véhicule facile", icon: Car },
  { code: "espace_rangement", label: "Espace de rangement / établi", icon: Wrench },
  { code: "cameras_surveillance", label: "Caméra de surveillance", icon: Camera },
  { code: "gardiennage", label: "Gardiennage / sécurité", icon: ShieldCheck },
];

// ---------- Terrain ----------
const TERRAIN: Equipement[] = [
  { code: "cloture", label: "Clôturé", icon: Fence },
  { code: "viabilise_eau", label: "Viabilisé — raccordement eau", icon: Droplet },
  { code: "viabilise_electricite", label: "Viabilisé — raccordement électricité", icon: Zap },
  { code: "acces_route_goudronnee", label: "Accès route goudronnée", icon: Route },
  { code: "titre_foncier", label: "Titre foncier disponible", icon: FileCheck },
  { code: "bornage_realise", label: "Bornage réalisé", icon: Map },
  { code: "arbore", label: "Arboré", icon: Trees },
  { code: "vue_degagee", label: "Vue dégagée", icon: Mountain },
];

export const EQUIPEMENTS_PAR_TYPE: Record<TypeBien, Equipement[]> = {
  appartement: RESIDENTIEL,
  maison: RESIDENTIEL,
  villa: RESIDENTIEL,
  bureau: BUREAU,
  magasin: MAGASIN,
  garage: GARAGE,
  terrain: TERRAIN,
};

/** Catalogue applicable à un type de bien donné (jamais vide). */
export function equipementsDisponibles(typeBien: TypeBien): Equipement[] {
  return EQUIPEMENTS_PAR_TYPE[typeBien] ?? RESIDENTIEL;
}

/** Libellé lisible d'un code d'équipement, quel que soit le type de bien
 * d'origine (utile en affichage, où on ne veut pas se limiter au catalogue
 * du type_bien courant si l'annonce a changé de type entretemps). */
export function libelleEquipement(code: string): string {
  for (const liste of Object.values(EQUIPEMENTS_PAR_TYPE)) {
    const trouve = liste.find((e) => e.code === code);
    if (trouve) return trouve.label;
  }
  return code;
}

/** Équipement (icône + libellé) par code, tous catalogues confondus. */
export function trouverEquipement(code: string): Equipement | undefined {
  for (const liste of Object.values(EQUIPEMENTS_PAR_TYPE)) {
    const trouve = liste.find((e) => e.code === code);
    if (trouve) return trouve;
  }
  return undefined;
}

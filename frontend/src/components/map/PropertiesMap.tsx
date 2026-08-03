import { useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { MessageCircle, CalendarPlus } from "lucide-react";
import type { Bien } from "../../types";

// --- Correctif icônes Leaflet ---
// Par défaut, react-leaflet/leaflet référence les icônes via des chemins relatifs
// qui cassent avec les bundlers (Vite). On reconstruit une icône par défaut
// à partir des assets fournis par le package `leaflet` lui-même.
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

const defaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = defaultIcon;

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const TYPE_LABELS: Record<string, string> = {
  maison: "Maison",
  appartement: "Appartement",
  magasin: "Magasin",
  garage: "Garage",
  bureau: "Bureau",
  terrain: "Terrain",
  villa: "Villa",
};

// Format compact pour tenir dans une bulle ("2,4M DH", "850k DH", "3.500 DH"),
// même logique visuelle que les puces de prix Google Maps / Booking.
function formatPrixPin(prix: number): string {
  if (prix >= 1_000_000) {
    const millions = prix / 1_000_000;
    return `${Number.isInteger(millions) ? millions.toFixed(0) : millions.toFixed(1)}M`;
  }
  if (prix >= 10_000) {
    const milliers = prix / 1_000;
    return `${Number.isInteger(milliers) ? milliers.toFixed(0) : milliers.toFixed(1)}k`;
  }
  return prix.toLocaleString("fr-MA");
}

// Icône "bulle de prix" : le div externe (className) est positionné par
// Leaflet exactement au point GPS (iconSize/iconAnchor à [0,0]) sans aucune
// taille propre ; la bulle réellement visible est le <span> interne, centré
// sur ce point via `transform: translate(-50%, -50%)` en CSS (voir
// index.css, classes .smartrent-pin-anchor / .smartrent-pin). Cette
// technique permet une bulle de largeur variable (prix courts vs longs)
// tout en restant parfaitement centrée sur les coordonnées du bien.
function buildPriceIcon(bien: Bien): L.DivIcon {
  const label = `${formatPrixPin(bien.prix)} DH`;
  return L.divIcon({
    className: "smartrent-pin-anchor",
    html: `<span class="smartrent-pin">${label}</span>`,
    iconSize: [0, 0],
    iconAnchor: [0, 0],
    popupAnchor: [0, -20],
  });
}

// Recentre la carte automatiquement quand la liste de biens filtrés change.
function FitBounds({ biens }: { biens: Bien[] }) {
  const map = useMap();
  const coords = biens
    .filter((b) => b.latitude != null && b.longitude != null)
    .map((b) => [b.latitude as number, b.longitude as number] as [number, number]);

  useMemo(() => {
    if (coords.length === 0) return;
    if (coords.length === 1) {
      map.setView(coords[0], 13);
    } else {
      map.fitBounds(L.latLngBounds(coords), { padding: [40, 40], maxZoom: 15 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(coords)]);

  return null;
}

// Centre par défaut : Maroc (utile quand aucun bien géolocalisé n'est visible)
const DEFAULT_CENTER: [number, number] = [31.7917, -7.0926];
const DEFAULT_ZOOM = 6;

export default function PropertiesMap({
  biens,
  onReserve,
  onContact,
}: {
  biens: Bien[];
  onReserve?: (bien: Bien) => void;
  onContact?: (bien: Bien) => void;
}) {
  const geoBiens = biens.filter((b) => b.latitude != null && b.longitude != null);

  return (
    <div className="overflow-hidden rounded-lg border border-[var(--color-line)]">
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom
        style={{ height: "520px", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitBounds biens={geoBiens} />
        {geoBiens.map((bien) => {
          const rawUrl = bien.photos && bien.photos.length > 0 ? bien.photos[0].url : null;
          const photoUrl = rawUrl
            ? rawUrl.startsWith("http://") || rawUrl.startsWith("https://")
              ? rawUrl
              : `${API_BASE_URL}${rawUrl}`
            : null;

          return (
            <Marker
              key={bien.id}
              position={[bien.latitude as number, bien.longitude as number]}
              icon={buildPriceIcon(bien)}
            >
              <Popup minWidth={220}>
                <div className="space-y-1.5">
                  {photoUrl && (
                    <img
                      src={photoUrl}
                      alt={bien.titre}
                      className="mb-1 h-24 w-full rounded object-cover"
                    />
                  )}
                  <p className="font-mono text-[10px] uppercase tracking-wide text-[#9c6b3f]">
                    {TYPE_LABELS[bien.type_bien] ?? bien.type_bien}
                  </p>
                  <p className="text-sm font-semibold leading-snug">{bien.titre}</p>
                  <p className="text-xs text-gray-600">{bien.ville}</p>
                  <p className="font-mono text-sm font-semibold">
                    {bien.prix.toLocaleString("fr-MA")} MAD{" "}
                    {bien.type_transaction !== "vente" && (
                      <span className="text-xs font-normal text-gray-500">/ mois</span>
                    )}
                  </p>
                  <div className="mt-2 flex gap-1.5">
                    {onContact && (
                      <button
                        type="button"
                        onClick={() => onContact(bien)}
                        className="flex flex-1 items-center justify-center gap-1 rounded border border-gray-300 py-1 text-xs font-medium hover:bg-gray-50"
                      >
                        <MessageCircle size={12} />
                        Contacter
                      </button>
                    )}
                    {onReserve && bien.statut === "disponible" && (
                      <button
                        type="button"
                        onClick={() => onReserve(bien)}
                        className="flex flex-1 items-center justify-center gap-1 rounded bg-[#c08552] py-1 text-xs font-medium text-white hover:bg-[#9c6b3f]"
                      >
                        <CalendarPlus size={12} />
                        {bien.type_transaction === "vente" ? "Faire une offre" : "Réserver"}
                      </button>
                    )}
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
      {biens.length > 0 && geoBiens.length < biens.length && (
        <p className="border-t border-[var(--color-line)] bg-[var(--color-paper-2)] px-3 py-1.5 text-xs text-[var(--color-ink-3)]">
          {biens.length - geoBiens.length} bien(s) non géolocalisé(s) — non affiché(s) sur la carte.
        </p>
      )}
    </div>
  );
}

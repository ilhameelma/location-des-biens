import { useEffect, useRef, useState } from "react";
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { Search, Loader2, X } from "lucide-react";

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

const DEFAULT_CENTER: [number, number] = [31.7917, -7.0926]; // Maroc
const DEFAULT_ZOOM = 5;

interface Suggestion {
  display_name: string;
  lat: string;
  lon: string;
}

function ClickHandler({ onPick }: { onPick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

// Recentre la carte par programmation (sélection d'une suggestion de recherche),
// contrairement à un clic sur la carte où la vue est déjà à la bonne position.
function FlyTo({ target }: { target: [number, number] | null }) {
  const map = useMap();
  useEffect(() => {
    if (target) map.flyTo(target, 15);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target?.[0], target?.[1]]);
  return null;
}

/**
 * Sélecteur de coordonnées GPS (étape 17 — Cartographie).
 * Barre de recherche d'adresse avec suggestions (autocomplete Nominatim/OSM,
 * gratuit, sans clé API) directement sur la carte, en plus du clic manuel pour
 * affiner l'emplacement exact du bien.
 */
export default function LocationPicker({
  latitude,
  longitude,
  ville,
  adresse,
  onChange,
}: {
  latitude: number | null;
  longitude: number | null;
  ville: string;
  adresse: string;
  onChange: (lat: number, lng: number) => void;
}) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [searching, setSearching] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [flyTarget, setFlyTarget] = useState<[number, number] | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const boxRef = useRef<HTMLDivElement>(null);

  const position: [number, number] | null =
    latitude != null && longitude != null ? [latitude, longitude] : null;

  // Ferme la liste de suggestions au clic en dehors de la zone recherche+carte.
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const runSearch = (text: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (text.trim().length < 3) {
      setSuggestions([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setSearching(true);
      setSearchError(null);
      try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&limit=5&countrycodes=ma&q=${encodeURIComponent(
          text
        )}`;
        const res = await fetch(url, { headers: { Accept: "application/json" } });
        if (!res.ok) throw new Error("indisponible");
        const data: Suggestion[] = await res.json();
        setSuggestions(data);
        setShowSuggestions(true);
        if (data.length === 0) setSearchError("Aucun résultat pour cette recherche.");
      } catch {
        setSearchError("Service de recherche indisponible — cliquez directement sur la carte.");
      } finally {
        setSearching(false);
      }
    }, 450);
  };

  const handleQueryChange = (value: string) => {
    setQuery(value);
    runSearch(value);
  };

  const handleSelectSuggestion = (s: Suggestion) => {
    const lat = parseFloat(s.lat);
    const lon = parseFloat(s.lon);
    onChange(lat, lon);
    setFlyTarget([lat, lon]);
    setQuery(s.display_name);
    setShowSuggestions(false);
  };

  const handlePrefillFromForm = () => {
    const prefill = [adresse, ville, "Maroc"].filter(Boolean).join(", ");
    if (prefill) handleQueryChange(prefill);
  };

  return (
    <div className="sm:col-span-2" ref={boxRef}>
      <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
        Position sur la carte (optionnel)
      </label>

      <div className="relative">
        <div className="relative">
          <Search
            size={14}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-ink-3)]"
          />
          <input
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            onFocus={() => {
              if (!query) handlePrefillFromForm();
              if (suggestions.length > 0) setShowSuggestions(true);
            }}
            placeholder="Rechercher une adresse (ex. Résidence les Jardins, Bouskoura)…"
            className="w-full rounded-md border border-[var(--color-line)] py-2 pl-9 pr-8 text-sm outline-none focus:border-[var(--color-brass)]"
          />
          {searching && (
            <Loader2
              size={14}
              className="absolute right-8 top-1/2 -translate-y-1/2 animate-spin text-[var(--color-ink-3)]"
            />
          )}
          {query && !searching && (
            <button
              type="button"
              onClick={() => {
                setQuery("");
                setSuggestions([]);
                setSearchError(null);
              }}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--color-ink-3)] hover:text-[var(--color-ink)]"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {showSuggestions && suggestions.length > 0 && (
          <ul className="absolute z-[1000] mt-1 max-h-56 w-full overflow-y-auto rounded-md border border-[var(--color-line)] bg-[var(--color-card)] shadow-lg">
            {suggestions.map((s, idx) => (
              <li key={idx}>
                <button
                  type="button"
                  onClick={() => handleSelectSuggestion(s)}
                  className="block w-full px-3 py-2 text-left text-xs text-[var(--color-ink-2)] hover:bg-[var(--color-paper-2)]"
                >
                  {s.display_name}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {searchError && <p className="mt-1 text-xs text-[var(--color-rust)]">{searchError}</p>}

      <div className="mt-2 overflow-hidden rounded-md border border-[var(--color-line)]">
        <MapContainer
          center={position ?? DEFAULT_CENTER}
          zoom={position ? 14 : DEFAULT_ZOOM}
          scrollWheelZoom={false}
          style={{ height: "260px", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <ClickHandler onPick={onChange} />
          <FlyTo target={flyTarget} />
          {position && <Marker position={position} />}
        </MapContainer>
      </div>
      <p className="mt-1 text-xs text-[var(--color-ink-3)]">
        {position
          ? `Position choisie : ${position[0].toFixed(5)}, ${position[1].toFixed(5)} — cherchez une autre adresse ou cliquez sur la carte pour ajuster.`
          : "Tapez une adresse ci-dessus et choisissez une suggestion, ou cliquez directement sur la carte."}
      </p>
    </div>
  );
}

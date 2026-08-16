import { StrictMode } from 'react'
import { createRoot, hydrateRoot } from 'react-dom/client'
import 'leaflet/dist/leaflet.css'
import './index.css'
import App from './App.tsx'
import { detecterEtAppliquerModeTv } from './lib/detectTv'

detecterEtAppliquerModeTv()

const rootElement = document.getElementById('root')!

// react-snap injecte du HTML statique dans #root au moment du build (pour
// que les bots IA/moteurs de recherche voient du vrai contenu). Si ce HTML
// est déjà présent, on "hydrate" par-dessus au lieu de tout re-render depuis
// zéro — sinon (dev local, npm run dev), comportement normal.
if (rootElement.hasChildNodes()) {
  hydrateRoot(
    rootElement,
    <StrictMode>
      <App />
    </StrictMode>,
  )
} else {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}

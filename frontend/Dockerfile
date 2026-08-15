# ============================================================
# SmartRent — Front-end React (Dockerfile)
# À placer à la racine de frontend/ (à côté de package.json, vite.config.ts...)
# Build multi-étapes : Node pour compiler, Nginx (léger) pour servir le
# résultat statique — l'image finale ne contient PAS node_modules/Vite.
# ============================================================

# --- Étape 1 : build Vite ---
FROM node:20-alpine AS build
WORKDIR /app

# Chromium nécessaire à react-snap (pré-rendu de la landing page pour les
# bots IA/SEO). On utilise le Chromium système plutôt que de laisser
# Puppeteer télécharger le sien (échoue souvent sur Alpine) — d'où ces
# variables d'env AVANT le npm ci.
RUN apk add --no-cache chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

COPY package.json package-lock.json ./
RUN npm install

COPY . .

# VITE_API_URL est injectée AU BUILD (Vite embarque les variables VITE_*
# dans le bundle JS final — impossible de les changer après coup sans
# rebuild, contrairement à une variable d'environnement classique).
# "/api" fonctionne car Nginx (voir nginx/nginx.conf) route déjà /api/
# vers le conteneur backend — pas besoin de connaître le domaine à l'avance.
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build

# --- Étape 2 : servir le build avec Nginx ---
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD wget -qO- http://localhost:80 || exit 1

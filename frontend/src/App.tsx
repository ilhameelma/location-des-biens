import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./lib/auth";
import ProtectedRoute from "./routes/ProtectedRoute";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import PublierPage from "./pages/PublierPage";
import ConditionsGeneralesPage from "./pages/ConditionsGeneralesPage";
import PolitiqueQualitePage from "./pages/PolitiqueQualitePage";
import ActualitesPubliquesPage from "./pages/ActualitesPubliquesPage";

import SearchPage from "./pages/client/SearchPage";
import ReservationsPage from "./pages/client/ReservationsPage";
import PaiementsPage from "./pages/client/PaiementsPage";
import MessagesPage from "./pages/client/MessagesPage";
import AvisPage from "./pages/client/AvisPage";
import FavorisPage from "./pages/client/FavorisPage";
import ClientReclamationsPage from "./pages/client/ReclamationsPage";
import ClientPublierPage from "./pages/client/PublierPage";

import OwnerDashboard from "./pages/proprietaire/OwnerDashboard";
import DemandesPage from "./pages/proprietaire/DemandesPage";
import OwnerPaiementsPage from "./pages/proprietaire/OwnerPaiementsPage";
import OwnerMessagesPage from "./pages/proprietaire/OwnerMessagesPage";
import OwnerAvisPage from "./pages/proprietaire/AvisPage";

import ProjetsPage from "./pages/promoteur/ProjetsPage";
import ProjetDetailPage from "./pages/promoteur/ProjetDetailPage";

import AdminDashboard from "./pages/admin/AdminDashboard";
import UtilisateursPage from "./pages/admin/UtilisateursPage";
import AnnoncesPage from "./pages/admin/AnnoncesPage";
import ReclamationsPage from "./pages/admin/ReclamationsPage";
import ActualitesPage from "./pages/admin/ActualitesPage";

import BienDetailPage from "./pages/BienDetailPage";
import ProprietairePublicPage from "./pages/ProprietairePublicPage";
import ComptePage from "./pages/ComptePage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Page d'accueil publique — accessible à tout visiteur, avant connexion/inscription */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/publier" element={<PublierPage />} />
          <Route path="/conditions-generales-utilisation" element={<ConditionsGeneralesPage />} />
          <Route path="/politique-qualite" element={<PolitiqueQualitePage />} />
          <Route path="/actualites" element={<ActualitesPubliquesPage />} />

          {/* Espace Client */}
          <Route path="/client" element={<ProtectedRoute role="client"><SearchPage /></ProtectedRoute>} />
          <Route path="/client/reservations" element={<ProtectedRoute role="client"><ReservationsPage /></ProtectedRoute>} />
          <Route path="/client/paiements" element={<ProtectedRoute role="client"><PaiementsPage /></ProtectedRoute>} />
          <Route path="/client/messages" element={<ProtectedRoute role="client"><MessagesPage /></ProtectedRoute>} />
          <Route path="/client/avis" element={<ProtectedRoute role="client"><AvisPage /></ProtectedRoute>} />
          <Route path="/client/favoris" element={<ProtectedRoute role="client"><FavorisPage /></ProtectedRoute>} />
          <Route path="/client/reclamations" element={<ProtectedRoute role="client"><ClientReclamationsPage /></ProtectedRoute>} />
          <Route path="/client/publier" element={<ProtectedRoute role="client"><ClientPublierPage /></ProtectedRoute>} />

          {/* Espace Propriétaire */}
          <Route path="/proprietaire" element={<ProtectedRoute role="proprietaire"><OwnerDashboard /></ProtectedRoute>} />
          <Route path="/proprietaire/demandes" element={<ProtectedRoute role="proprietaire"><DemandesPage /></ProtectedRoute>} />
          <Route path="/proprietaire/paiements" element={<ProtectedRoute role="proprietaire"><OwnerPaiementsPage /></ProtectedRoute>} />
          <Route path="/proprietaire/messages" element={<ProtectedRoute role="proprietaire"><OwnerMessagesPage /></ProtectedRoute>} />
          <Route path="/proprietaire/avis" element={<ProtectedRoute role="proprietaire"><OwnerAvisPage /></ProtectedRoute>} />

          {/* Espace Agence immobilière — mêmes écrans que Propriétaire (biens,
              demandes, paiements, messages, avis), génériques sur le rôle
              connecté ; seul le formulaire de publication change (champs
              mandant optionnels, voir OwnerDashboard.tsx). */}
          <Route path="/agence" element={<ProtectedRoute role="agence"><OwnerDashboard /></ProtectedRoute>} />
          <Route path="/agence/demandes" element={<ProtectedRoute role="agence"><DemandesPage /></ProtectedRoute>} />
          <Route path="/agence/paiements" element={<ProtectedRoute role="agence"><OwnerPaiementsPage /></ProtectedRoute>} />
          <Route path="/agence/messages" element={<ProtectedRoute role="agence"><OwnerMessagesPage /></ProtectedRoute>} />
          <Route path="/agence/avis" element={<ProtectedRoute role="agence"><OwnerAvisPage /></ProtectedRoute>} />

          {/* Espace Conciergerie — idem, formulaire de publication avec
              mandant_nom obligatoire (voir OwnerDashboard.tsx). */}
          <Route path="/conciergerie" element={<ProtectedRoute role="conciergerie"><OwnerDashboard /></ProtectedRoute>} />
          <Route path="/conciergerie/demandes" element={<ProtectedRoute role="conciergerie"><DemandesPage /></ProtectedRoute>} />
          <Route path="/conciergerie/paiements" element={<ProtectedRoute role="conciergerie"><OwnerPaiementsPage /></ProtectedRoute>} />
          <Route path="/conciergerie/messages" element={<ProtectedRoute role="conciergerie"><OwnerMessagesPage /></ProtectedRoute>} />
          <Route path="/conciergerie/avis" element={<ProtectedRoute role="conciergerie"><OwnerAvisPage /></ProtectedRoute>} />

          {/* Espace Promoteur immobilier — "Mes biens" liste tous les lots
              (lecture/édition/suppression) mais la publication se fait
              exclusivement depuis un projet (Mes projets → lot). */}
          <Route path="/promoteur" element={<ProtectedRoute role="promoteur"><OwnerDashboard /></ProtectedRoute>} />
          <Route path="/promoteur/projets" element={<ProtectedRoute role="promoteur"><ProjetsPage /></ProtectedRoute>} />
          <Route path="/promoteur/projets/:id" element={<ProtectedRoute role="promoteur"><ProjetDetailPage /></ProtectedRoute>} />
          <Route path="/promoteur/demandes" element={<ProtectedRoute role="promoteur"><DemandesPage /></ProtectedRoute>} />
          <Route path="/promoteur/paiements" element={<ProtectedRoute role="promoteur"><OwnerPaiementsPage /></ProtectedRoute>} />
          <Route path="/promoteur/messages" element={<ProtectedRoute role="promoteur"><OwnerMessagesPage /></ProtectedRoute>} />
          <Route path="/promoteur/avis" element={<ProtectedRoute role="promoteur"><OwnerAvisPage /></ProtectedRoute>} />

          {/* Fiche détaillée d'une annonce — accessible aux rôles connectés (client, tous les annonceurs, admin) */}
          <Route path="/biens/:id" element={<ProtectedRoute><BienDetailPage /></ProtectedRoute>} />

          {/* Fiche profil publique d'un annonceur (ses annonces + note moyenne) — accessible à tous */}
          <Route path="/proprietaires/:id" element={<ProtectedRoute><ProprietairePublicPage /></ProtectedRoute>} />

          {/* Mon compte — accessible à tous les rôles connectés */}
          <Route path="/compte" element={<ProtectedRoute><ComptePage /></ProtectedRoute>} />

          {/* Espace Admin */}
          <Route path="/admin" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/utilisateurs" element={<ProtectedRoute role="admin"><UtilisateursPage /></ProtectedRoute>} />
          <Route path="/admin/biens" element={<ProtectedRoute role="admin"><AnnoncesPage /></ProtectedRoute>} />
          <Route path="/admin/reclamations" element={<ProtectedRoute role="admin"><ReclamationsPage /></ProtectedRoute>} />
          <Route path="/admin/actualites" element={<ProtectedRoute role="admin"><ActualitesPage /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

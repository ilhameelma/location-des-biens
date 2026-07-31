import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./lib/auth";
import ProtectedRoute from "./routes/ProtectedRoute";
import LoginPage from "./pages/LoginPage";

import SearchPage from "./pages/client/SearchPage";
import ReservationsPage from "./pages/client/ReservationsPage";
import PaiementsPage from "./pages/client/PaiementsPage";
import MessagesPage from "./pages/client/MessagesPage";
import AvisPage from "./pages/client/AvisPage";

import OwnerDashboard from "./pages/proprietaire/OwnerDashboard";
import DemandesPage from "./pages/proprietaire/DemandesPage";
import OwnerPaiementsPage from "./pages/proprietaire/OwnerPaiementsPage";
import OwnerMessagesPage from "./pages/proprietaire/OwnerMessagesPage";
import OwnerAvisPage from "./pages/proprietaire/AvisPage";

import AdminDashboard from "./pages/admin/AdminDashboard";
import UtilisateursPage from "./pages/admin/UtilisateursPage";
import AnnoncesPage from "./pages/admin/AnnoncesPage";
import ReclamationsPage from "./pages/admin/ReclamationsPage";

import BienDetailPage from "./pages/BienDetailPage";
import ComptePage from "./pages/ComptePage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />

          {/* Espace Client */}
          <Route path="/client" element={<ProtectedRoute role="client"><SearchPage /></ProtectedRoute>} />
          <Route path="/client/reservations" element={<ProtectedRoute role="client"><ReservationsPage /></ProtectedRoute>} />
          <Route path="/client/paiements" element={<ProtectedRoute role="client"><PaiementsPage /></ProtectedRoute>} />
          <Route path="/client/messages" element={<ProtectedRoute role="client"><MessagesPage /></ProtectedRoute>} />
          <Route path="/client/avis" element={<ProtectedRoute role="client"><AvisPage /></ProtectedRoute>} />

          {/* Espace Propriétaire */}
          <Route path="/proprietaire" element={<ProtectedRoute role="proprietaire"><OwnerDashboard /></ProtectedRoute>} />
          <Route path="/proprietaire/demandes" element={<ProtectedRoute role="proprietaire"><DemandesPage /></ProtectedRoute>} />
          <Route path="/proprietaire/paiements" element={<ProtectedRoute role="proprietaire"><OwnerPaiementsPage /></ProtectedRoute>} />
          <Route path="/proprietaire/messages" element={<ProtectedRoute role="proprietaire"><OwnerMessagesPage /></ProtectedRoute>} />
          <Route path="/proprietaire/avis" element={<ProtectedRoute role="proprietaire"><OwnerAvisPage /></ProtectedRoute>} />

          {/* Fiche détaillée d'une annonce — accessible aux 3 rôles (client, propriétaire, admin) */}
          <Route path="/biens/:id" element={<ProtectedRoute><BienDetailPage /></ProtectedRoute>} />

          {/* Mon compte — accessible aux 3 rôles (client, propriétaire, admin) */}
          <Route path="/compte" element={<ProtectedRoute><ComptePage /></ProtectedRoute>} />

          {/* Espace Admin */}
          <Route path="/admin" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/utilisateurs" element={<ProtectedRoute role="admin"><UtilisateursPage /></ProtectedRoute>} />
          <Route path="/admin/biens" element={<ProtectedRoute role="admin"><AnnoncesPage /></ProtectedRoute>} />
          <Route path="/admin/reclamations" element={<ProtectedRoute role="admin"><ReclamationsPage /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

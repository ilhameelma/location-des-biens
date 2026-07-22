import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useAuth } from "../lib/auth";
import type { Role } from "../types";
import DashboardLayout from "../components/layout/DashboardLayout";

export default function ProtectedRoute({
  role,
  children,
}: {
  role: Role;
  children: ReactNode;
}) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--color-paper)] text-sm text-[var(--color-ink-2)]">
        Chargement…
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={`/${user.role}`} replace />;

  return <DashboardLayout>{children}</DashboardLayout>;
}

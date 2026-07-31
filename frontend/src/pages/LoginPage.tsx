import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Home, Building2, Users, Key } from "lucide-react";
import { useAuth } from "../lib/auth";
import type { Role } from "../types";
import logo from "../assets/logo_immo1.png";

const ROLE_CARDS: { role: Role; label: string; icon: typeof Home }[] = [
  { role: "client", label: "Client", icon: Key },
  { role: "proprietaire", label: "Propriétaire", icon: Building2 },
  { role: "admin", label: "Administrateur", icon: Users },
];

export default function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [role, setRole] = useState<Role>("client");
  const [nom, setNom] = useState("");
  const [prenom, setPrenom] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [telephone, setTelephone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user =
        mode === "login"
          ? await login(email, password)
          : await register({ nom, prenom, email, password, telephone, role });
      navigate(`/${user.role}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Une erreur est survenue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-ink)] px-4">
      <div className="w-full max-w-md">
        

        <form onSubmit={handleSubmit} className="rounded-lg bg-[var(--color-card)] p-8 shadow-xl">
          {/* Logo */}

  <div className="mb-6 flex justify-center">
    <img
      src={logo}
      alt="ImmoVision"
      className="h-24 w-auto object-contain"
    />
  </div>

          <div className="mb-5 flex gap-1 rounded-md bg-[var(--color-paper-2)] p-1">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`flex-1 rounded py-1.5 text-sm font-medium transition-colors ${
                mode === "login" ? "bg-white shadow-sm text-[var(--color-ink)]" : "text-[var(--color-ink-2)]"
              }`}
            >
              Connexion
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`flex-1 rounded py-1.5 text-sm font-medium transition-colors ${
                mode === "register" ? "bg-white shadow-sm text-[var(--color-ink)]" : "text-[var(--color-ink-2)]"
              }`}
            >
              Inscription
            </button>
          </div>

          {mode === "register" && (
            <>
              <div className="mb-3 grid grid-cols-3 gap-2">
                {ROLE_CARDS.map((c) => (
                  <button
                    type="button"
                    key={c.role}
                    onClick={() => setRole(c.role)}
                    className={`flex flex-col items-center gap-1.5 rounded-md border p-2.5 text-center transition-colors ${
                      role === c.role
                        ? "border-[var(--color-brass)] bg-[#f4e9df]"
                        : "border-[var(--color-line)] hover:border-[var(--color-ink-3)]"
                    }`}
                  >
                    <c.icon size={16} className="text-[var(--color-ink)]" />
                    <span className="text-[11px] font-medium text-[var(--color-ink)]">{c.label}</span>
                  </button>
                ))}
              </div>
              <div className="mb-3 grid grid-cols-2 gap-2">
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Prénom</label>
                  <input
                    required
                    value={prenom}
                    onChange={(e) => setPrenom(e.target.value)}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Nom</label>
                  <input
                    required
                    value={nom}
                    onChange={(e) => setNom(e.target.value)}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                </div>
              </div>
              <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
                Téléphone (optionnel)
              </label>
              <input
                value={telephone}
                onChange={(e) => setTelephone(e.target.value)}
                className="mb-3 w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
              />
            </>
          )}

          <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Email</label>
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mb-3 w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
          />
          <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">Mot de passe</label>
          <input
            required
            type="password"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mb-5 w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
          />

          {error && (
            <div className="mb-4 rounded-md bg-[var(--color-rust-bg)] px-3 py-2 text-xs text-[var(--color-rust)]">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-[var(--color-brass)] py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
          >
            {loading ? "Chargement…" : mode === "login" ? "Se connecter" : "Créer mon compte"}
          </button>
        </form>
      </div>
    </div>
  );
}

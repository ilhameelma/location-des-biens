import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Home, Building2, Users, Key, HardHat, Handshake, ArrowLeft } from "lucide-react";
import { useAuth } from "../lib/auth";
import type { Role } from "../types";
import logo from "../assets/logo_immo1.png";

const ROLE_CARDS: { role: Role; label: string; icon: typeof Home }[] = [
  { role: "client", label: "Client", icon: Key },
  { role: "proprietaire", label: "Propriétaire", icon: Home },
  { role: "agence", label: "Agence immobilière", icon: Building2 },
  { role: "promoteur", label: "Promoteur immobilier", icon: HardHat },
  { role: "courtier", label: "Courtier (Samsar)", icon: Handshake },
  { role: "admin", label: "Administrateur", icon: Users },
];

// Rôles professionnels nécessitant des champs d'inscription supplémentaires.
const ROLES_PRO: Role[] = ["agence", "promoteur", "courtier"];

export default function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // La landing page peut renvoyer directement sur l'onglet "Inscription"
  // via le lien /login?mode=register (bouton "Inscription" du header public).
  const [mode, setMode] = useState<"login" | "register">(
    searchParams.get("mode") === "register" ? "register" : "login"
  );
  const [role, setRole] = useState<Role>("client");
  const [nom, setNom] = useState("");
  const [prenom, setPrenom] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [telephone, setTelephone] = useState("");
  const [raisonSociale, setRaisonSociale] = useState("");
  const [numeroRc, setNumeroRc] = useState("");
  const [numeroCartePro, setNumeroCartePro] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const estPro = ROLES_PRO.includes(role);
  const raisonSocialeObligatoire = role === "agence" || role === "promoteur";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user =
        mode === "login"
          ? await login(email, password)
          : await register({
              nom,
              prenom,
              email,
              password,
              telephone,
              role,
              raison_sociale: estPro ? raisonSociale : undefined,
              numero_rc: estPro ? numeroRc : undefined,
              numero_carte_pro: role === "courtier" ? numeroCartePro : undefined,
            });
      navigate(`/${user.role}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Une erreur est survenue");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-ink)] px-4 py-10">
      <div className="w-full max-w-md">
        <Link
          to="/"
          className="mb-4 inline-flex items-center gap-1.5 text-sm text-[var(--color-paper-2)] transition-colors hover:text-white"
        >
          <ArrowLeft size={15} />
          Retour à l'accueil
        </Link>

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
                    <span className="text-[11px] font-medium leading-tight text-[var(--color-ink)]">
                      {c.label}
                    </span>
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

              {estPro && (
                <div className="mb-3 rounded-md border border-[var(--color-line)] bg-[var(--color-paper-2)] p-3">
                  <p className="mb-2 text-[11px] font-medium text-[var(--color-ink-2)]">
                    Informations professionnelles
                  </p>
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
                    {role === "promoteur" ? "Raison sociale (société de promotion)" : "Raison sociale (nom de l'agence)"}
                    {raisonSocialeObligatoire && " *"}
                  </label>
                  <input
                    required={raisonSocialeObligatoire}
                    value={raisonSociale}
                    onChange={(e) => setRaisonSociale(e.target.value)}
                    className="mb-2 w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                  <label className="mb-1 block text-xs font-medium text-[var(--color-ink-2)]">
                    {role === "promoteur" ? "N° registre de commerce / agrément (optionnel)" : "N° registre de commerce (optionnel)"}
                  </label>
                  <input
                    value={numeroRc}
                    onChange={(e) => setNumeroRc(e.target.value)}
                    className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                  />
                  {role === "courtier" && (
                    <>
                      <label className="mb-1 mt-2 block text-xs font-medium text-[var(--color-ink-2)]">
                        N° de carte professionnelle (optionnel)
                      </label>
                      <input
                        value={numeroCartePro}
                        onChange={(e) => setNumeroCartePro(e.target.value)}
                        className="w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]"
                      />
                    </>
                  )}
                </div>
              )}
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

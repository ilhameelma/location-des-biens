import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Home, Building2, Key, HardHat, Handshake, X } from "lucide-react";
import { useAuth } from "../lib/auth";
import type { Role } from "../types";
import SiteFooter from "../components/layout/SiteFooter";
import logo from "../assets/logo_immo1.png";

const ROLE_CARDS: { role: Role; label: string; icon: typeof Home }[] = [
  { role: "client", label: "Client", icon: Key },
  { role: "proprietaire", label: "Propriétaire", icon: Home },
  { role: "agence", label: "Agence immobilière", icon: Building2 },
  { role: "promoteur", label: "Promoteur immobilier", icon: HardHat },
  { role: "conciergerie", label: "Conciergerie", icon: Handshake },
  // "admin" volontairement absent : le rôle Administrateur ne doit jamais
  // pouvoir être créé depuis le formulaire d'inscription public. Le compte
  // admin existe déjà en base ; la connexion (onglet "Connexion") reste
  // inchangée pour ce rôle.
];

// Rôles professionnels nécessitant des champs d'inscription supplémentaires.
const ROLES_PRO: Role[] = ["agence", "promoteur", "conciergerie"];

export default function LoginPage() {
  const { user, login, register, resendVerification, verifyEmail } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // La landing page peut renvoyer directement sur l'onglet "Inscription"
  // via le lien /login?mode=register (bouton "Inscription" du header public).
  // Le bouton global "Publier une annonce" (PublierAnnonceButton.tsx) va plus
  // loin : il ajoute aussi ?role=... pour présélectionner directement le bon
  // profil (agence/promoteur/conciergerie/propriétaire) — évite qu'un visiteur
  // publie une annonce en créant sans s'en rendre compte un compte "Client"
  // (carte sélectionnée par défaut jusqu'ici).
  const roleParam = searchParams.get("role") as Role | null;
  const roleParamValide: Role | null =
    roleParam && ROLE_CARDS.some((c) => c.role === roleParam) ? roleParam : null;

  const [mode, setMode] = useState<"login" | "register">(
    searchParams.get("mode") === "register" || roleParamValide ? "register" : "login"
  );
  const [role] = useState<Role>(roleParamValide ?? "client");
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
  // Contient l'email en attente de confirmation (après inscription, ou après
  // une tentative de connexion sur un compte pas encore confirmé) : tant
  // qu'il n'est pas null, le panneau de saisie du code OTP s'affiche à la
  // place du formulaire, pas de redirection automatique.
  const [inscriptionEnAttente, setInscriptionEnAttente] = useState<string | null>(null);
  const [renvoiEnvoye, setRenvoiEnvoye] = useState(false);
  // Code à 6 chiffres saisi par l'utilisateur, reçu par email.
  const [otpCode, setOtpCode] = useState("");
  const [otpError, setOtpError] = useState<string | null>(null);
  const [otpVerifying, setOtpVerifying] = useState(false);
  // Affiche un message de succès sur l'écran de connexion juste après
  // confirmation du code, pour rassurer l'utilisateur avant qu'il se connecte.
  const [codeConfirme, setCodeConfirme] = useState(false);

  const estPro = ROLES_PRO.includes(role);
  const raisonSocialeObligatoire = role === "agence" || role === "promoteur";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setRenvoiEnvoye(false);
    setCodeConfirme(false);
    setLoading(true);
    try {
      if (mode === "register") {
        const res = await register({
          nom,
          prenom,
          email,
          password,
          telephone,
          role,
          raison_sociale: estPro ? raisonSociale : undefined,
          numero_rc: estPro ? numeroRc : undefined,
          numero_carte_pro: role === "conciergerie" ? numeroCartePro : undefined,
        });
        setOtpCode("");
        setOtpError(null);
        setInscriptionEnAttente(res.email);
      } else {
        const user = await login(email, password);
        navigate(`/${user.role}`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Une erreur est survenue";
      if (mode === "login" && message.toLowerCase().includes("non confirmée")) {
        // Compte existant mais email pas encore confirmé : plutôt qu'un simple
        // message d'erreur, on propose directement la saisie du code reçu par
        // email (un nouveau code est envoyé pour que l'ancien, potentiellement
        // oublié/expiré, ne soit pas le seul recours).
        setOtpCode("");
        setOtpError(null);
        setInscriptionEnAttente(email);
        resendVerification(email).catch(() => {});
      } else {
        setError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRenvoyerConfirmation = async () => {
    if (!inscriptionEnAttente) return;
    setLoading(true);
    try {
      await resendVerification(inscriptionEnAttente);
      setRenvoiEnvoye(true);
    } catch {
      // best-effort : même en cas d'échec réseau, on ne bloque pas l'utilisateur
      setRenvoiEnvoye(true);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifierCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inscriptionEnAttente) return;
    setOtpError(null);
    setOtpVerifying(true);
    try {
      await verifyEmail(inscriptionEnAttente, otpCode);
      setEmail(inscriptionEnAttente);
      setPassword("");
      setInscriptionEnAttente(null);
      setOtpCode("");
      setCodeConfirme(true);
      setMode("login");
    } catch (err) {
      setOtpError(err instanceof Error ? err.message : "Code invalide ou expiré");
    } finally {
      setOtpVerifying(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-[var(--color-ink)]">
      <div className="flex flex-1 items-center justify-center px-3 py-6 sm:px-4 sm:py-10">
      <div className="w-full max-w-md">
        {inscriptionEnAttente ? (
          <div className="relative rounded-lg bg-[var(--color-card)] p-5 text-center shadow-xl sm:p-8">
            <button
              type="button"
              onClick={() => navigate(user ? `/${user.role}` : "/")}
              aria-label={user ? "Annuler et retourner à mon espace" : "Annuler et retourner à l'accueil"}
              title={user ? "Annuler et retourner à mon espace" : "Annuler et retourner à l'accueil"}
              className="absolute right-3 top-3 rounded-full p-1.5 text-[var(--color-ink-3)] transition-colors hover:bg-[var(--color-paper-2)] hover:text-[var(--color-ink)]"
            >
              <X size={18} />
            </button>
            <Link to="/" className="mb-6 flex justify-center" aria-label="Retour à l'accueil">
              <img src={logo} alt="ImmoVision" className="h-24 w-auto object-contain" />
            </Link>
            <h2 className="mb-2 text-base font-semibold text-[var(--color-ink)]">
              Entrez votre code de vérification
            </h2>
            <p className="mb-5 text-sm text-[var(--color-ink-2)]">
              Un code à 6 chiffres a été envoyé à{" "}
              <span className="font-medium text-[var(--color-ink)]">{inscriptionEnAttente}</span>.
              Saisissez-le ci-dessous pour activer votre compte (pensez à vérifier vos spams,
              le code expire après 15 minutes).
            </p>

            <form onSubmit={handleVerifierCode}>
              <input
                required
                autoFocus
                inputMode="numeric"
                pattern="\d{6}"
                maxLength={6}
                placeholder="••••••"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                className="mb-3 w-full rounded-md border border-[var(--color-line)] px-3 py-2.5 text-center text-lg tracking-[0.5em] outline-none focus:border-[var(--color-brass)]"
              />

              {otpError && (
                <p className="mb-3 rounded-md bg-[var(--color-rust-bg)] px-3 py-2 text-xs text-[var(--color-rust)]">
                  {otpError}
                </p>
              )}
              {renvoiEnvoye && !otpError && (
                <p className="mb-3 text-xs text-[var(--color-brass-deep)]">
                  Un nouveau code vient d'être envoyé.
                </p>
              )}

              <button
                type="submit"
                disabled={otpVerifying || otpCode.length !== 6}
                className="mb-3 w-full rounded-md bg-[var(--color-brass)] py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
              >
                {otpVerifying ? "Vérification…" : "Vérifier le code"}
              </button>
            </form>

            <button
              type="button"
              onClick={handleRenvoyerConfirmation}
              disabled={loading}
              className="mb-3 w-full rounded-md border border-[var(--color-line)] py-2.5 text-sm font-medium text-[var(--color-ink)] transition-colors hover:bg-[var(--color-paper-2)] disabled:opacity-60"
            >
              Renvoyer le code
            </button>
            <button
              type="button"
              onClick={() => {
                setInscriptionEnAttente(null);
                setOtpCode("");
                setOtpError(null);
                setMode("login");
              }}
              className="w-full text-xs font-medium text-[var(--color-ink-2)] underline transition-colors hover:text-[var(--color-ink)]"
            >
              Retour à la connexion
            </button>
          </div>
        ) : (
        <form onSubmit={handleSubmit} className="relative rounded-lg bg-[var(--color-card)] p-5 shadow-xl sm:p-8">
          <button
            type="button"
            onClick={() => navigate(user ? `/${user.role}` : "/")}
            aria-label={user ? "Annuler et retourner à mon espace" : "Annuler et retourner à l'accueil"}
            title={user ? "Annuler et retourner à mon espace" : "Annuler et retourner à l'accueil"}
            className="absolute right-3 top-3 rounded-full p-1.5 text-[var(--color-ink-3)] transition-colors hover:bg-[var(--color-paper-2)] hover:text-[var(--color-ink)]"
          >
            <X size={18} />
          </button>
          {/* Logo */}

  <Link to="/" className="mb-6 flex justify-center" aria-label="Retour à l'accueil">
    <img
      src={logo}
      alt="ImmoVision"
      className="h-24 w-auto object-contain"
    />
  </Link>

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
              {roleParamValide && (
                <div className="mb-3 flex items-center justify-between rounded-md border border-[var(--color-brass)] bg-[#f4e9df] px-3 py-2.5">
                  <span className="flex items-center gap-2 text-sm font-medium text-[var(--color-ink)]">
                    {(() => {
                      const c = ROLE_CARDS.find((c) => c.role === roleParamValide)!;
                      return (
                        <>
                          <c.icon size={16} className="text-[var(--color-brass-deep)]" />
                          Inscription — {c.label}
                        </>
                      );
                    })()}
                  </span>
                  <Link
                    to="/publier"
                    className="text-xs font-medium text-[var(--color-ink-2)] underline hover:text-[var(--color-ink)]"
                  >
                    Changer
                  </Link>
                </div>
              )}
              <div className="mb-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
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
                  {role === "conciergerie" && (
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
            onChange={(e) => {
              setEmail(e.target.value);
              setCodeConfirme(false);
            }}
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

          {mode === "login" && codeConfirme && !error && (
            <div className="mb-4 rounded-md bg-[#eaf3ea] px-3 py-2 text-xs text-green-700">
              Email confirmé — vous pouvez vous connecter.
            </div>
          )}

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
        )}

      </div>
      </div>
      <SiteFooter />
    </div>
  );
}

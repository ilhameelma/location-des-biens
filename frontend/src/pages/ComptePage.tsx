import { useState, type FormEvent } from "react";
import { User, Mail, Phone, ShieldCheck, KeyRound, CalendarDays, Briefcase } from "lucide-react";
import { useAuth } from "../lib/auth";
import { ROLE_LABELS } from "../lib/roles";

const STATUT_LABEL: Record<string, { label: string; className: string }> = {
  verifie: { label: "Vérifié", className: "bg-[#e7f3ea] text-[#2f6b3f]" },
  en_attente: { label: "En attente de vérification", className: "bg-[#fbf1de] text-[#9a6a12]" },
  rejete: { label: "Rejeté", className: "bg-[var(--color-rust-bg)] text-[var(--color-rust)]" },
};

const inputClass =
  "w-full rounded-md border border-[var(--color-line)] px-3 py-2 text-sm outline-none focus:border-[var(--color-brass)]";
const labelClass = "mb-1 block text-xs font-medium text-[var(--color-ink-2)]";

export default function ComptePage() {
  const { user, updateProfile, changePassword } = useAuth();

  // --- Formulaire profil ---
  const [nom, setNom] = useState(user?.nom ?? "");
  const [prenom, setPrenom] = useState(user?.prenom ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [telephone, setTelephone] = useState(user?.telephone ?? "");
  const [raisonSociale, setRaisonSociale] = useState(user?.raison_sociale ?? "");
  const [numeroRc, setNumeroRc] = useState(user?.numero_rc ?? "");
  const [numeroCartePro, setNumeroCartePro] = useState(user?.numero_carte_pro ?? "");
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null);

  // --- Formulaire mot de passe ---
  const [ancienMdp, setAncienMdp] = useState("");
  const [nouveauMdp, setNouveauMdp] = useState("");
  const [confirmMdp, setConfirmMdp] = useState("");
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdError, setPwdError] = useState<string | null>(null);
  const [pwdSuccess, setPwdSuccess] = useState<string | null>(null);

  if (!user) return null;

  const statut = STATUT_LABEL[user.statut_verification];

  const handleProfileSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setProfileError(null);
    setProfileSuccess(null);
    setProfileLoading(true);
    try {
      await updateProfile({
        nom: nom.trim(),
        prenom: prenom.trim(),
        email: email.trim(),
        telephone: telephone.trim() || undefined,
        raison_sociale: raisonSociale.trim() || undefined,
        numero_rc: numeroRc.trim() || undefined,
        numero_carte_pro: numeroCartePro.trim() || undefined,
      });
      setProfileSuccess("Informations mises à jour avec succès.");
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : "Une erreur est survenue");
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setPwdError(null);
    setPwdSuccess(null);

    if (nouveauMdp !== confirmMdp) {
      setPwdError("La confirmation ne correspond pas au nouveau mot de passe.");
      return;
    }
    if (nouveauMdp.length < 8) {
      setPwdError("Le nouveau mot de passe doit contenir au moins 8 caractères.");
      return;
    }

    setPwdLoading(true);
    try {
      await changePassword(ancienMdp, nouveauMdp);
      setPwdSuccess("Mot de passe modifié avec succès.");
      setAncienMdp("");
      setNouveauMdp("");
      setConfirmMdp("");
    } catch (err) {
      setPwdError(err instanceof Error ? err.message : "Une erreur est survenue");
    } finally {
      setPwdLoading(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h1 className="tick-rule font-display text-2xl text-[var(--color-ink)]">Mon compte</h1>

      {/* En-tête résumé */}
      <div className="mt-6 flex items-center gap-4 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-5">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-paper-2)] font-display text-xl text-[var(--color-ink)]">
          {user.prenom[0]}
          {user.nom[0]}
        </div>
        <div className="flex-1">
          <p className="font-display text-lg text-[var(--color-ink)]">
            {user.prenom} {user.nom}
          </p>
          <p className="font-mono text-xs text-[var(--color-ink-3)]">{ROLE_LABELS[user.role]}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {statut && (
            <span className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${statut.className}`}>
              <ShieldCheck size={12} />
              {statut.label}
            </span>
          )}
          <span className="flex items-center gap-1 font-mono text-[11px] text-[var(--color-ink-3)]">
            <CalendarDays size={12} />
            Membre depuis {new Date(user.date_creation).toLocaleDateString("fr-MA")}
          </span>
        </div>
      </div>

      {/* Informations personnelles */}
      <form
        onSubmit={handleProfileSubmit}
        className="mt-6 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-6"
      >
        <h2 className="mb-4 flex items-center gap-2 font-display text-base text-[var(--color-ink)]">
          <User size={16} className="text-[var(--color-brass)]" />
          Informations personnelles
        </h2>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>Prénom</label>
            <input required value={prenom} onChange={(e) => setPrenom(e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Nom</label>
            <input required value={nom} onChange={(e) => setNom(e.target.value)} className={inputClass} />
          </div>
        </div>

        <div className="mt-3">
          <label className={labelClass}>
            <span className="flex items-center gap-1">
              <Mail size={12} /> Email
            </span>
          </label>
          <input
            required
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass}
          />
        </div>

        <div className="mt-3">
          <label className={labelClass}>
            <span className="flex items-center gap-1">
              <Phone size={12} /> Téléphone
            </span>
          </label>
          <input
            value={telephone}
            onChange={(e) => setTelephone(e.target.value)}
            placeholder="Ajouter un numéro de téléphone"
            className={inputClass}
          />
        </div>

        {(user.role === "agence" || user.role === "promoteur" || user.role === "courtier") && (
          <div className="mt-4 rounded-md border border-[var(--color-line)] bg-[var(--color-paper-2)] p-3">
            <p className="mb-2 flex items-center gap-1 text-[11px] font-medium text-[var(--color-ink-2)]">
              <Briefcase size={12} /> Informations professionnelles
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className={labelClass}>Raison sociale</label>
                <input
                  value={raisonSociale}
                  onChange={(e) => setRaisonSociale(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>
                  {user.role === "courtier" ? "N° registre de commerce" : "N° registre de commerce / agrément"}
                </label>
                <input
                  value={numeroRc}
                  onChange={(e) => setNumeroRc(e.target.value)}
                  className={inputClass}
                />
              </div>
              {user.role === "courtier" && (
                <div>
                  <label className={labelClass}>N° carte professionnelle (optionnel)</label>
                  <input
                    value={numeroCartePro}
                    onChange={(e) => setNumeroCartePro(e.target.value)}
                    className={inputClass}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {profileError && (
          <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-3 py-2 text-xs text-[var(--color-rust)]">
            {profileError}
          </div>
        )}
        {profileSuccess && (
          <div className="mt-4 rounded-md bg-[#e7f3ea] px-3 py-2 text-xs text-[#2f6b3f]">{profileSuccess}</div>
        )}

        <button
          type="submit"
          disabled={profileLoading}
          className="mt-5 rounded-md bg-[var(--color-brass)] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)] disabled:opacity-60"
        >
          {profileLoading ? "Enregistrement…" : "Enregistrer les modifications"}
        </button>
      </form>

      {/* Mot de passe */}
      <form
        onSubmit={handlePasswordSubmit}
        className="mt-6 rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-6"
      >
        <h2 className="mb-4 flex items-center gap-2 font-display text-base text-[var(--color-ink)]">
          <KeyRound size={16} className="text-[var(--color-brass)]" />
          Changer le mot de passe
        </h2>

        <label className={labelClass}>Mot de passe actuel</label>
        <input
          required
          type="password"
          value={ancienMdp}
          onChange={(e) => setAncienMdp(e.target.value)}
          className={`mb-3 ${inputClass}`}
        />

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>Nouveau mot de passe</label>
            <input
              required
              type="password"
              minLength={8}
              value={nouveauMdp}
              onChange={(e) => setNouveauMdp(e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>Confirmer le nouveau mot de passe</label>
            <input
              required
              type="password"
              minLength={8}
              value={confirmMdp}
              onChange={(e) => setConfirmMdp(e.target.value)}
              className={inputClass}
            />
          </div>
        </div>

        {pwdError && (
          <div className="mt-4 rounded-md bg-[var(--color-rust-bg)] px-3 py-2 text-xs text-[var(--color-rust)]">
            {pwdError}
          </div>
        )}
        {pwdSuccess && (
          <div className="mt-4 rounded-md bg-[#e7f3ea] px-3 py-2 text-xs text-[#2f6b3f]">{pwdSuccess}</div>
        )}

        <button
          type="submit"
          disabled={pwdLoading}
          className="mt-5 rounded-md border border-[var(--color-ink)] px-4 py-2 text-sm font-medium text-[var(--color-ink)] transition-colors hover:bg-[var(--color-ink)] hover:text-white disabled:opacity-60"
        >
          {pwdLoading ? "Modification…" : "Modifier le mot de passe"}
        </button>
      </form>
    </div>
  );
}

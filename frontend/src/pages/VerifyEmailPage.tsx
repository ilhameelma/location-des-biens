import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle2, XCircle, Loader2, ArrowLeft } from "lucide-react";
import { useAuth } from "../lib/auth";
import Footer from "../components/layout/Footer";
import logo from "../assets/logo_immo1.png";

type Etat = "en_cours" | "succes" | "echec";

export default function VerifyEmailPage() {
  const { verifyEmail } = useAuth();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");

  const [etat, setEtat] = useState<Etat>("en_cours");
  const [message, setMessage] = useState<string | null>(null);
  // Évite un double appel (StrictMode / re-render) qui invaliderait le token
  // à usage unique avant même d'avoir affiché le résultat du premier appel.
  const dejaAppele = useRef(false);

  useEffect(() => {
    if (!token) {
      setEtat("echec");
      setMessage("Lien de vérification invalide : aucun token fourni.");
      return;
    }
    if (dejaAppele.current) return;
    dejaAppele.current = true;

    verifyEmail(token)
      .then(() => setEtat("succes"))
      .catch((err) => {
        setEtat("echec");
        setMessage(err instanceof Error ? err.message : "Une erreur est survenue.");
      });
  }, [token, verifyEmail]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-ink)] px-4 py-10">
      <div className="w-full max-w-md">
        <div className="rounded-lg bg-[var(--color-card)] p-8 text-center shadow-xl">
          <div className="mb-6 flex justify-center">
            <img src={logo} alt="ImmoVision" className="h-24 w-auto object-contain" />
          </div>

          {etat === "en_cours" && (
            <>
              <Loader2 className="mx-auto mb-4 animate-spin text-[var(--color-brass)]" size={40} />
              <p className="text-sm text-[var(--color-ink-2)]">Vérification de votre email…</p>
            </>
          )}

          {etat === "succes" && (
            <>
              <CheckCircle2 className="mx-auto mb-4 text-green-600" size={40} />
              <h2 className="mb-2 text-base font-semibold text-[var(--color-ink)]">
                Email confirmé
              </h2>
              <p className="mb-5 text-sm text-[var(--color-ink-2)]">
                Votre adresse email a bien été vérifiée. Vous pouvez maintenant vous connecter.
              </p>
              <Link
                to="/login"
                className="inline-flex w-full items-center justify-center rounded-md bg-[var(--color-brass)] py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--color-brass-deep)]"
              >
                Se connecter
              </Link>
            </>
          )}

          {etat === "echec" && (
            <>
              <XCircle className="mx-auto mb-4 text-[var(--color-rust)]" size={40} />
              <h2 className="mb-2 text-base font-semibold text-[var(--color-ink)]">
                Vérification impossible
              </h2>
              <p className="mb-5 text-sm text-[var(--color-ink-2)]">
                {message ?? "Ce lien est invalide ou a expiré."}
              </p>
              <Link
                to="/login"
                className="inline-flex w-full items-center justify-center gap-1.5 rounded-md border border-[var(--color-line)] py-2.5 text-sm font-medium text-[var(--color-ink)] transition-colors hover:bg-[var(--color-paper-2)]"
              >
                <ArrowLeft size={15} />
                Retour à la connexion
              </Link>
            </>
          )}
        </div>

        <div className="mt-6">
          <Footer variant="dark" />
        </div>
      </div>
    </div>
  );
}

import { AlertTriangle, CheckCircle2 } from "lucide-react";
import type { FraudeResponse } from "../../types";

export default function FraudCheckResult({ result }: { result: FraudeResponse }) {
  return (
    <div
      className={`mt-2 rounded-md p-3 text-xs ${
        result.est_suspect
          ? "bg-[var(--color-rust-bg)] text-[var(--color-rust)]"
          : "bg-[var(--color-sage-bg)] text-[var(--color-sage)]"
      }`}
    >
      <div className="flex items-center gap-1.5 font-medium">
        {result.est_suspect ? <AlertTriangle size={13} /> : <CheckCircle2 size={13} />}
        {result.est_suspect ? "Annonce suspecte" : "Aucune anomalie détectée"}
      </div>
      <p className="mt-1">{result.raison}</p>
      <p className="mt-1 opacity-80">
        Prix attendu : {result.prix_attendu_dh.toLocaleString("fr-MA")} MAD — écart{" "}
        {result.ecart_prix_pct >= 0 ? "+" : ""}
        {Math.round(result.ecart_prix_pct * 100)}%
      </p>
    </div>
  );
}

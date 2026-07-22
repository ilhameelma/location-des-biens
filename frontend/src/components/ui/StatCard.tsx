import type { LucideIcon } from "lucide-react";

export default function StatCard({
  label,
  value,
  icon: Icon,
  trend,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
  trend?: string;
}) {
  return (
    <div className="rounded-lg border border-[var(--color-line)] bg-[var(--color-card)] p-5">
      <div className="flex items-start justify-between">
        <span className="text-sm text-[var(--color-ink-2)]">{label}</span>
        <Icon size={18} className="text-[var(--color-brass)]" />
      </div>
      <div className="mt-3 font-display text-2xl text-[var(--color-ink)]">{value}</div>
      {trend && <div className="mt-1 text-xs font-mono text-[var(--color-sage)]">{trend}</div>}
    </div>
  );
}

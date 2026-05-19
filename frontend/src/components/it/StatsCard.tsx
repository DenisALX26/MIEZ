import type { IconType } from "react-icons";

interface StatCardProps {
  title: string;
  value: number;
  icon: IconType;
  iconColor: string;
  suffix?: string;
  sub?: string;
}

const StatCard = ({ title, value, icon: Icon, suffix, sub }: StatCardProps) => {
  return (
    <article className="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 w-full flex items-start justify-between gap-3">
      <div className="flex flex-col">
        <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted-foreground)] font-medium">{title}</p>
        <p className="text-2xl font-semibold mt-1 tracking-tight">
          {value}
          {suffix ? <span className="text-base font-medium text-[var(--muted-foreground)] ml-1">{suffix}</span> : null}
        </p>
        {sub && <p className="text-xs text-[var(--muted-foreground)] mt-1">{sub}</p>}
      </div>
      <div className="w-10 h-10 rounded-xl bg-[var(--input-background)] grid place-items-center text-[var(--primary)] shrink-0">
        <Icon size={18} />
      </div>
    </article>
  );
};

export default StatCard;

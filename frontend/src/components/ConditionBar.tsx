export default function ConditionBar({ label, value }: { label: string; value: number }) {
  const color = value >= 75 ? 'bg-profit' : value >= 50 ? 'bg-accent' : 'bg-danger';
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="w-20 text-white/60">{label}</div>
      <div className="flex-1 h-2 bg-white/10 rounded-full">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <div className="w-8 text-right font-bold">{value}</div>
    </div>
  );
}

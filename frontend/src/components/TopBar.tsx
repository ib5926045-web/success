import { useStore } from '../store';
import { byn } from '../format';
import { Coins, Star, CalendarDays } from 'lucide-react';

export default function TopBar() {
  const me = useStore((s) => s.me);
  if (!me) return null;
  const xpPct = me.next_level_xp ? Math.min(100, Math.round((me.experience / me.next_level_xp) * 100)) : 100;
  return (
    <div className="sticky top-0 z-10 bg-graphite/95 backdrop-blur border-b border-white/10 px-4 py-2.5">
      <div className="flex items-center gap-2.5">
        <div className="w-9 h-9 rounded-full bg-accent/20 flex items-center justify-center text-lg font-bold text-accent overflow-hidden">
          {me.photo_url ? <img src={me.photo_url} className="w-full h-full object-cover" /> : (me.first_name?.[0] || 'П')}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-bold truncate">{me.first_name || 'Перекуп'} · Ур. {me.level} {me.level_name}</div>
          <div className="h-1.5 bg-white/10 rounded-full mt-1">
            <div className="h-full bg-accent rounded-full" style={{ width: `${xpPct}%` }} />
          </div>
        </div>
        <div className="text-right text-xs text-white/60">
          <div className="flex items-center gap-1 justify-end"><CalendarDays size={12} /> День {me.current_game_day}</div>
          <div className="flex items-center gap-1 justify-end mt-0.5"><Star size={12} className="text-accent" /> Реп. {me.reputation}/100</div>
        </div>
      </div>
      <div className="flex items-center gap-1.5 mt-1.5 text-accent font-bold text-lg">
        <Coins size={18} /> {byn(me.balance)}
      </div>
    </div>
  );
}

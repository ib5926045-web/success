import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useStore } from '../store';
import { byn, carTitle, riskLabel, riskColor } from '../format';
import CarVisual from '../components/CarVisual';
import { RefreshCw, Flame, Gauge, Cog } from 'lucide-react';
import { haptic, hideMainButton } from '../telegram';

export default function Market() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const patchMe = useStore((s) => s.patchMe);
  const nav = useNavigate();

  const load = async () => {
    setLoading(true);
    setErr('');
    try {
      const m = await api.market();
      setData(m);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    hideMainButton();
    load();
    api.me().then((m) => patchMe(m)).catch(() => {});
  }, []);

  const refresh = async (advance: boolean) => {
    try {
      haptic('select');
      const m = await api.refreshMarket(advance);
      setData(m);
      const me = await api.me();
      patchMe(me);
      haptic('success');
    } catch (e: any) {
      setErr(e.message);
      haptic('error');
    }
  };

  if (loading) return <div className="p-6 text-center text-white/60">Загружаем рынок…</div>;

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">🚗 Рынок · день {data?.game_day}</h1>
      </div>
      {err && <div className="card text-danger text-sm">{err}</div>}
      <div className="grid grid-cols-2 gap-2">
        <button className="btn-ghost text-sm" onClick={() => refresh(true)}>⏭ След. день</button>
        <button className="btn-ghost text-sm flex items-center justify-center gap-1" onClick={() => refresh(false)}>
          <RefreshCw size={14} /> Обновить{data?.refresh_cost ? ` · ${data.refresh_cost}` : ' · 0'}
        </button>
      </div>
      {(data?.cars || []).map((c: any) => (
        <div key={c.id} className="card cursor-pointer active:scale-[0.99] transition" onClick={() => nav(`/car/${c.id}`)}>
          <div className="flex gap-3">
            <div className="w-28 shrink-0"><CarVisual seed={c.image_seed} /></div>
            <div className="flex-1 min-w-0">
              <div className="font-bold text-sm leading-tight">{carTitle(c)}</div>
              <div className="text-xs text-white/50 flex items-center gap-2 mt-1">
                <span className="flex items-center gap-1"><Gauge size={12} />{(c.mileage / 1000).toFixed(0)} тыс.</span>
                <span className="flex items-center gap-1"><Cog size={12} />{c.transmission}</span>
              </div>
              <div className="text-accent font-bold mt-1">{byn(c.price)}</div>
              <div className="flex gap-1 mt-1.5 flex-wrap">
                <span className="chip bg-white/10 text-white/70">Ликв.: {c.liquidity}</span>
                <span className={`chip ${riskColor(c.risk_hint)}`}>{riskLabel(c.risk_hint)}</span>
                {c.urgent && <span className="chip bg-danger/20 text-danger flex items-center gap-1"><Flame size={11} />Срочно</span>}
              </div>
            </div>
          </div>
          <div className="text-xs text-white/50 mt-2 line-clamp-2">{c.short_description}</div>
        </div>
      ))}
      {data?.cars?.length === 0 && <div className="card text-center text-white/60">Объявления закончились. Перейдите к следующему дню.</div>}
    </div>
  );
}

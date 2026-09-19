import { useEffect, useState } from 'react';
import { api } from '../api';
import { useStore } from '../store';
import { byn } from '../format';
import { haptic, hideMainButton } from '../telegram';

export default function Deals() {
  const [listings, setListings] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [msg, setMsg] = useState('');
  const [counter, setCounter] = useState<Record<number, string>>({});
  const patchMe = useStore((s) => s.patchMe);

  const load = async () => {
    try {
      setListings(await api.listings());
      setHistory(await api.history());
    } catch {}
  };

  useEffect(() => { hideMainButton(); load(); }, []);

  const act = async (fn: () => Promise<any>, okMsg?: string) => {
    try {
      const r = await fn();
      if (r?.balance !== undefined) patchMe({ balance: r.balance });
      if (r?.experience !== undefined) patchMe({ experience: r.experience, level: r.level, reputation: r.reputation });
      setMsg(okMsg || r?.message || 'Готово');
      haptic('success');
      await load();
      const me = await api.me().catch(() => null);
      if (me) patchMe(me);
    } catch (e: any) {
      setMsg('❌ ' + e.message);
      haptic('error');
    }
  };

  const active = listings.filter((l) => l.status === 'ACTIVE');

  return (
    <div className="p-4 space-y-3">
      <h1 className="text-xl font-bold">🤝 Сделки</h1>
      {msg && <div className="card text-sm">{msg}</div>}
      {active.length === 0 && <div className="card text-white/60 text-sm">Нет активных объявлений. Выставьте машину из гаража.</div>}
      {active.map((l) => (
        <div key={l.id} className="card">
          <div className="font-bold text-sm">{l.car_title}</div>
          <div className="text-xs text-white/50">Цена: {byn(l.listing_price)} · Статус: {l.status}</div>
          <div className="space-y-2 mt-2">
            {l.offers.filter((o: any) => o.status === 'PENDING').map((o: any) => (
              <div key={o.id} className="bg-white/5 rounded-xl p-3">
                <div className="flex justify-between items-center">
                  <b className="text-sm">🧑 {o.buyer_name} <span className="text-white/40 font-normal">({o.buyer_type})</span></b>
                  <b className="text-accent">{byn(o.offered_price)}</b>
                </div>
                <div className="text-xs text-white/60 mt-1">«{o.message}»</div>
                <div className="grid grid-cols-3 gap-1.5 mt-2">
                  <button className="btn-accent text-xs !py-2" onClick={() => act(() => api.acceptOffer(l.id, o.id))}>Принять</button>
                  <button className="btn-ghost text-xs !py-2" onClick={() => act(() => api.declineOffer(l.id, o.id), 'Отклонено')}>Отказ</button>
                  <div className="flex gap-1">
                    <input className="!py-1.5 text-xs" placeholder="Цена" value={counter[o.id] || ''} onChange={(e) => setCounter({ ...counter, [o.id]: e.target.value })} />
                  </div>
                </div>
                {counter[o.id] && (
                  <button className="btn-ghost text-xs w-full mt-1.5 !py-2" onClick={() => act(() => api.counterOffer(l.id, o.id, Number(counter[o.id])))}>Встречная: {counter[o.id]}</button>
                )}
              </div>
            ))}
            {l.offers.every((o: any) => o.status !== 'PENDING') && <div className="text-xs text-white/40">Предложений пока нет.</div>}
          </div>
        </div>
      ))}

      <h2 className="font-bold mt-4">📜 История операций</h2>
      {history.slice(0, 20).map((t: any) => (
        <div key={t.id} className="card !py-2.5 flex justify-between text-sm">
          <div>
            <b>{t.type}</b>
            <div className="text-xs text-white/50">{t.meta?.title || t.meta?.reason || t.meta?.car_id ? `авто #${t.meta.car_id}` : ''} {t.meta?.profit !== undefined ? `· прибыль ${t.meta.profit}` : ''}</div>
          </div>
          <div className={`font-bold ${t.amount >= 0 ? 'text-profit' : 'text-danger'}`}>{t.amount >= 0 ? '+' : ''}{t.amount}</div>
        </div>
      ))}
    </div>
  );
}

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { byn } from '../format';
import CarVisual from '../components/CarVisual';
import { hideMainButton, haptic } from '../telegram';

export default function Garage() {
  const [cars, setCars] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const nav = useNavigate();

  useEffect(() => {
    hideMainButton();
    api.garage().then(setCars).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-center text-white/60">Открываем гараж…</div>;
  if (!cars.length)
    return (
      <div className="p-4">
        <h1 className="text-xl font-bold mb-3">🏠 Гараж пуст</h1>
        <div className="card text-center text-white/60">
          Купите первую машину на рынке. Начните с Passat B5 или Golf 4 — они ликвидные.
        </div>
        <button className="btn-accent w-full mt-3" onClick={() => { haptic('select'); nav('/'); }}>На рынок</button>
      </div>
    );

  return (
    <div className="p-4 space-y-3">
      <h1 className="text-xl font-bold">🏠 Гараж · {cars.length}</h1>
      {cars.map((c) => (
        <div key={c.id} className="card cursor-pointer" onClick={() => nav(`/garage/${c.id}`)}>
          <div className="flex gap-3">
            <div className="w-28 shrink-0"><CarVisual seed={c.image_seed} /></div>
            <div className="flex-1">
              <div className="font-bold text-sm">{c.brand} {c.model} · {c.year}</div>
              <div className="text-xs text-white/50">Куплена: {byn(c.purchase_price || 0)} · Вложено: {byn(c.invested)}</div>
              <div className="text-xs text-white/50">Оценка: <b className="text-white">{byn(c.estimated_value)}</b></div>
              <div className={`font-bold ${c.potential_profit >= 0 ? 'text-profit' : 'text-danger'}`}>
                {c.potential_profit >= 0 ? '+' : ''}{byn(c.potential_profit).replace(' BYN', '')} BYN
              </div>
              <div className="flex gap-1 mt-1">
                <span className="chip bg-white/10">Готовность {c.readiness}%</span>
                {c.status === 'LISTED' && <span className="chip bg-accent/20 text-accent">На продаже</span>}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

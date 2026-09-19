import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useStore } from '../store';
import { byn } from '../format';
import CarVisual from '../components/CarVisual';
import ConditionBar from '../components/ConditionBar';
import { haptic, showBack, hideMainButton } from '../telegram';

const STYLES = [
  { v: 'honest', label: 'Честное описание' },
  { v: 'pros', label: 'Акцент на достоинства' },
  { v: 'urgent', label: 'Срочная продажа' },
  { v: 'premium', label: 'Премиальная подача' },
];

export default function GarageCar() {
  const { id } = useParams();
  const nav = useNavigate();
  const [data, setData] = useState<any>(null);
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);
  const [price, setPrice] = useState('');
  const [style, setStyle] = useState('honest');
  const [promo, setPromo] = useState(0);
  const patchMe = useStore((s) => s.patchMe);

  const load = async () => {
    try {
      const d = await api.garageCar(Number(id));
      setData(d);
      if (!price) setPrice(String(d.car.estimated_value));
    } catch (e: any) {
      setMsg(e.message);
    }
  };

  useEffect(() => {
    load();
    showBack(true, () => nav('/garage'));
    return () => { showBack(false); hideMainButton(); };
  }, [id]);

  const repair = async (t: string) => {
    setBusy(true);
    try {
      const r = await api.repair(Number(id), t);
      patchMe({ balance: r.balance });
      setMsg(`✅ ${r.result_text} (−${r.cost} BYN)`);
      haptic('success');
      await load();
    } catch (e: any) {
      setMsg('❌ ' + e.message);
      haptic('error');
    } finally {
      setBusy(false);
    }
  };

  const prepare = async (a: string) => {
    try {
      const r = await api.prepare(Number(id), a);
      setMsg('✅ ' + r.message);
      haptic('success');
      await load();
    } catch (e: any) {
      setMsg('❌ ' + e.message);
    }
  };

  const list = async () => {
    setBusy(true);
    try {
      const r = await api.list(Number(id), { listing_price: Number(price), listing_style: style, promotion_level: promo });
      setMsg(`✅ Объявление размещено! Предложений: ${r.offers_count}`);
      haptic('success');
      await load();
    } catch (e: any) {
      setMsg('❌ ' + e.message);
      haptic('error');
    } finally {
      setBusy(false);
    }
  };

  if (!data) return <div className="p-6 text-center text-white/60">Загрузка…</div>;
  const c = data.car;

  return (
    <div className="p-4 space-y-3 pb-24">
      <CarVisual seed={c.image_seed} big />
      <h1 className="text-lg font-bold">{c.brand} {c.model} · {c.year}</h1>
      <div className="card grid grid-cols-3 gap-2 text-center text-sm">
        <div><div className="text-white/50 text-xs">Куплена</div><b>{byn(c.purchase_price || 0)}</b></div>
        <div><div className="text-white/50 text-xs">Вложено</div><b>{byn(c.invested)}</b></div>
        <div><div className="text-white/50 text-xs">Оценка</div><b className="text-accent">{byn(c.estimated_value)}</b></div>
      </div>
      {msg && <div className="card text-sm">{msg}</div>}
      <div className="card space-y-1.5">
        <div className="font-bold text-sm">Состояние · готовность {c.readiness}%</div>
        <ConditionBar label="Кузов" value={c.conditions.body} />
        <ConditionBar label="Двигатель" value={c.conditions.engine} />
        <ConditionBar label="Коробка" value={c.conditions.gearbox} />
        <ConditionBar label="Подвеска" value={c.conditions.suspension} />
        <ConditionBar label="Салон" value={c.conditions.interior} />
        {c.known_defects?.length > 0 && (
          <div className="text-xs text-accent mt-1">Нюансы: {c.known_defects.join('; ')}</div>
        )}
      </div>

      {data.listing ? (
        <div className="card">
          <div className="font-bold text-sm">📢 На продаже: {byn(data.listing.price)}</div>
          <div className="text-xs text-white/50">Предложений: {data.offers?.length || 0}. Управляйте ими на вкладке «Сделки».</div>
          <button className="btn-ghost w-full mt-2 text-sm" onClick={async () => { await api.unlist(Number(id)); await load(); }}>Снять с продажи</button>
        </div>
      ) : (
        <>
          <div className="card">
            <div className="font-bold text-sm mb-2">🔧 Ремонт и подготовка</div>
            <div className="grid grid-cols-2 gap-2">
              {(data.repairs || []).map((r: any) => (
                <button key={r.type} disabled={busy || r.locked} onClick={() => repair(r.type)} className="btn-ghost text-xs">
                  {r.locked ? `🔒 ${r.label}` : `${r.label} · ${r.min}–${r.max}`}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-2 mt-2">
              <button onClick={() => prepare('photo')} className="btn-ghost text-xs">{data.photo_done ? '✓ Фото готово' : '📸 Сделать фото (0)'}</button>
              <button onClick={() => prepare('ad')} className="btn-ghost text-xs">📝 Честное описание</button>
            </div>
          </div>
          <div className="card">
            <div className="font-bold text-sm mb-2">📢 Выставить на продажу</div>
            <input value={price} onChange={(e) => setPrice(e.target.value)} type="number" placeholder="Цена продажи" />
            <div className="grid grid-cols-2 gap-2 mt-2">
              {STYLES.map((s) => (
                <button key={s.v} onClick={() => setStyle(s.v)} className={style === s.v ? 'btn-accent text-xs' : 'btn-ghost text-xs'}>{s.label}</button>
              ))}
            </div>
            <div className="grid grid-cols-3 gap-2 mt-2">
              {[0, 1, 2].map((p) => (
                <button key={p} onClick={() => setPromo(p)} className={promo === p ? 'btn-accent text-xs' : 'btn-ghost text-xs'}>
                  {p === 0 ? 'Без продвижения' : p === 1 ? 'ТОП · 60' : 'Турбо · 150'}
                </button>
              ))}
            </div>
            <button disabled={busy || !price} onClick={list} className="btn-accent w-full mt-2">Выставить за {price ? byn(Number(price)) : '…'}</button>
          </div>
        </>
      )}
    </div>
  );
}

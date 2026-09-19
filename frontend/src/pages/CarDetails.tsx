import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useStore } from '../store';
import { byn, carTitle, riskColor } from '../format';
import CarVisual from '../components/CarVisual';
import ConditionBar from '../components/ConditionBar';
import { haptic, mainButton, hideMainButton, showBack } from '../telegram';

const INSPECTIONS = [
  { type: 'body', label: 'Осмотреть кузов', price: 30 },
  { type: 'docs', label: 'Проверить документы', price: 40 },
  { type: 'diagnostics', label: 'Диагностика', price: 50 },
  { type: 'testdrive', label: 'Тест-драйв', price: 30 },
  { type: 'full', label: 'Комплексная (120)', price: 120 },
];

export default function CarDetails() {
  const { id } = useParams();
  const nav = useNavigate();
  const [car, setCar] = useState<any>(null);
  const [err, setErr] = useState('');
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);
  const [offer, setOffer] = useState('');
  const [tips, setTips] = useState<string[]>([]);
  const patchMe = useStore((s) => s.patchMe);

  const load = async () => {
    try {
      const c = await api.car(Number(id));
      setCar(c);
      api.advisor(Number(id)).then((a) => setTips(a.tips)).catch(() => {});
    } catch (e: any) {
      setErr(e.message);
    }
  };

  useEffect(() => {
    load();
    showBack(true, () => nav('/'));
    return () => { showBack(false); hideMainButton(); };
  }, [id]);

  useEffect(() => {
    if (car) {
      mainButton(`Купить за ${car.price.toLocaleString('ru-RU')} BYN`, () => buy());
    }
  }, [car?.price]);

  const buy = async () => {
    if (!car || busy) return;
    setBusy(true);
    setMsg('');
    try {
      const r = await api.buy(car.id);
      patchMe({ balance: r.balance, experience: r.experience, level: r.level });
      haptic('success');
      nav('/garage');
    } catch (e: any) {
      setMsg(e.message);
      haptic('error');
    } finally {
      setBusy(false);
    }
  };

  const inspect = async (t: string) => {
    setBusy(true);
    setMsg('');
    try {
      const r = await api.inspect(car.id, t);
      patchMe({ balance: r.balance });
      setMsg(r.result_text);
      haptic('success');
      await load();
    } catch (e: any) {
      setMsg(e.message);
      haptic('error');
    } finally {
      setBusy(false);
    }
  };

  const haggle = async (discount?: number) => {
    setBusy(true);
    setMsg('');
    try {
      const body = discount ? { discount_percent: discount } : { offer_price: Number(offer) };
      const r = await api.negotiate(car.id, body);
      const prefix = r.result === 'ACCEPTED' ? '✅ Принято! ' : r.result === 'COUNTERED' ? '🤝 Встречное: ' : '❌ Отказ. ';
      setMsg(prefix + r.message);
      haptic(r.result === 'DECLINED' ? 'error' : 'success');
      await load();
    } catch (e: any) {
      setMsg(e.message);
      haptic('error');
    } finally {
      setBusy(false);
    }
  };

  if (err && !car) return <div className="p-4"><div className="card text-danger">{err}</div></div>;
  if (!car) return <div className="p-6 text-center text-white/60">Загрузка…</div>;

  return (
    <div className="p-4 space-y-3 pb-24">
      <CarVisual seed={car.image_seed} big />
      <div>
        <h1 className="text-lg font-bold">{carTitle(car)}</h1>
        <div className="text-xs text-white/50">{car.color} · {car.engine_volume} {car.engine_type} · {car.power_hp} л.с. · {car.transmission} · {car.drive_type}</div>
      </div>
      <div className="card">
        <div className="flex items-end justify-between">
          <div>
            <div className="text-xs text-white/50">Цена продавца</div>
            <div className="text-2xl font-bold text-accent">{byn(car.price)}</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-white/50">Рынок</div>
            <div className="text-sm font-bold">{byn(car.market_value_low)} – {byn(car.market_value_high)}</div>
          </div>
        </div>
        <div className="text-xs text-white/60 mt-2">🧑‍💼 {car.seller_personality_label} · Владельцев: {car.owners_count} · {car.urgent ? '🔥 Срочно!' : ''}</div>
        <div className="text-sm mt-1">{car.description}</div>
      </div>

      {msg && <div className="card text-sm border-accent/30">{msg}</div>}

      <div className="card space-y-1.5">
        <div className="text-sm font-bold mb-1">Состояние (видимое)</div>
        <ConditionBar label="Кузов" value={car.conditions.body} />
        <ConditionBar label="Двигатель" value={car.conditions.engine} />
        <ConditionBar label="Коробка" value={car.conditions.gearbox} />
        <ConditionBar label="Подвеска" value={car.conditions.suspension} />
        <ConditionBar label="Салон" value={car.conditions.interior} />
      </div>

      {(car.visible_defects?.length > 0 || car.known_defects?.length > 0) && (
        <div className="card text-sm">
          <div className="font-bold mb-1">Известные нюансы</div>
          {car.visible_defects?.map((d: string, i: number) => <div key={i} className="text-white/70">👁 {d}</div>)}
          {car.known_defects?.map((d: string, i: number) => <div key={i} className="text-accent">🔍 {d}</div>)}
        </div>
      )}

      <div className="card">
        <div className="font-bold mb-2 text-sm">🔎 Проверки</div>
        <div className="grid grid-cols-2 gap-2">
          {INSPECTIONS.map((i) => (
            <button key={i.type} disabled={busy || car.inspections_done?.includes(i.type)} onClick={() => inspect(i.type)}
              className={car.inspections_done?.includes(i.type) ? 'btn-ghost text-xs opacity-50' : 'btn-ghost text-xs'}>
              {car.inspections_done?.includes(i.type) ? '✓ ' : ''}{i.label} · {i.price}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="font-bold mb-2 text-sm">🤝 Торг</div>
        <div className="grid grid-cols-3 gap-2">
          {[3, 5, 8].map((d) => (
            <button key={d} disabled={busy} onClick={() => haggle(d)} className="btn-ghost text-sm">−{d}%</button>
          ))}
        </div>
        <div className="flex gap-2 mt-2">
          <input value={offer} onChange={(e) => setOffer(e.target.value)} placeholder="Своя цена, BYN" type="number" />
          <button disabled={busy || !offer} onClick={() => haggle()} className="btn-accent text-sm whitespace-nowrap">Предложить</button>
        </div>
      </div>

      {tips.length > 0 && (
        <div className="card text-sm">
          <div className="font-bold mb-1">🔧 Совет механика</div>
          {tips.map((t, i) => <div key={i} className="text-white/70 mb-1">• {t}</div>)}
        </div>
      )}

      <button disabled={busy} onClick={buy} className="btn-accent w-full text-lg">Купить за {byn(car.price)}</button>
      <div className={riskColor('medium') + ' hidden'} />
    </div>
  );
}

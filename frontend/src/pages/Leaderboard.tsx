import { useEffect, useState } from 'react';
import { api } from '../api';
import { byn } from '../format';
import { hideMainButton } from '../telegram';

const SORTS = [
  { v: 'capital', label: 'Капитал' },
  { v: 'profit', label: 'Прибыль' },
  { v: 'reputation', label: 'Репутация' },
  { v: 'deals', label: 'Сделки' },
];

export default function Leaderboard() {
  const [data, setData] = useState<any>(null);
  const [sort, setSort] = useState('capital');

  useEffect(() => {
    hideMainButton();
    api.leaderboard(sort).then(setData).catch(() => {});
  }, [sort]);

  return (
    <div className="p-4 space-y-3">
      <h1 className="text-xl font-bold">🏆 Рейтинг</h1>
      <div className="grid grid-cols-4 gap-1.5">
        {SORTS.map((s) => (
          <button key={s.v} onClick={() => setSort(s.v)} className={sort === s.v ? 'btn-accent text-xs !py-2' : 'btn-ghost text-xs !py-2'}>{s.label}</button>
        ))}
      </div>
      {data?.my_rank && <div className="card text-sm">Ваше место: <b className="text-accent">#{data.my_rank}</b></div>}
      {(data?.rows || []).map((r: any) => (
        <div key={r.rank} className={`card !py-2.5 flex items-center gap-3 ${r.is_me ? 'border-accent/50' : ''}`}>
          <div className="font-bold text-accent w-8">#{r.rank}</div>
          <div className="flex-1">
            <div className="font-bold text-sm">{r.name} <span className="text-white/40 font-normal">· ур. {r.level}</span></div>
            <div className="text-xs text-white/50">Капитал {byn(r.capital)} · +{byn(r.profit).replace(' BYN', '')} · реп. {r.reputation}</div>
          </div>
        </div>
      ))}
      {(!data?.rows || !data.rows.length) && <div className="card text-white/60 text-sm">Пока пусто. Станьте первым!</div>}
    </div>
  );
}

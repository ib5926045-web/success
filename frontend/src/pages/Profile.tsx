import { useEffect, useState } from 'react';
import { api } from '../api';
import { useStore } from '../store';
import { byn } from '../format';
import { hideMainButton, haptic, shareScore } from '../telegram';

export default function Profile() {
  const me = useStore((s) => s.me);
  const patchMe = useStore((s) => s.patchMe);
  const [dash, setDash] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    hideMainButton();
    api.dashboard().then(setDash).catch(() => {});
    api.tasks().then(setTasks).catch(() => {});
    api.events().then(setEvents).catch(() => {});
  }, []);

  const claim = async (id: number) => {
    try {
      const r = await api.claimTask(id);
      patchMe({ balance: r.balance, experience: r.experience, level: r.level });
      setTasks(await api.tasks());
      haptic('success');
    } catch (e: any) {
      setMsg(e.message);
      haptic('error');
    }
  };

  const toggleRating = async () => {
    const r = await api.patchSettings({ rating_opt_out: !me?.rating_opt_out });
    patchMe({ rating_opt_out: r.rating_opt_out });
  };

  return (
    <div className="p-4 space-y-3">
      <h1 className="text-xl font-bold">👤 Профиль</h1>
      {msg && <div className="card text-danger text-sm">{msg}</div>}
      <div className="card">
        <div className="font-bold">{me?.first_name || 'Перекуп'} · Ур. {me?.level} {me?.level_name}</div>
        <div className="text-sm text-white/60">Баланс: <b className="text-accent">{byn(me?.balance || 0)}</b></div>
        {dash && (
          <div className="mt-2">
            <div className="text-xs text-white/50">Капитал {byn(dash.capital)} / цель {byn(dash.season_goal)} — {dash.goal_progress}%</div>
            <div className="h-2 bg-white/10 rounded-full mt-1">
              <div className="h-full bg-profit rounded-full" style={{ width: `${dash.goal_progress}%` }} />
            </div>
            <div className="text-xs text-white/50 mt-1">Сделок: {me?.deals_count} · Прибыль: {byn(me?.total_profit || 0)} · Серия: {me?.streak_days} дн.</div>
          </div>
        )}
        <button className="btn-ghost w-full mt-2 text-sm" onClick={() => shareScore(`Я заработал ${byn(me?.total_profit || 0)} в Перекуп Симуляторе. Сможешь больше?`)}>📤 Поделиться результатом</button>
      </div>

      <div className="card">
        <div className="font-bold text-sm mb-2">📋 Задания дня</div>
        {tasks.map((t) => (
          <div key={t.id} className="flex items-center gap-2 py-1.5 border-b border-white/5 last:border-0">
            <div className="flex-1 text-sm">
              <div>{t.title}</div>
              <div className="text-xs text-white/50">{t.progress_value}/{t.target_value} · 🎁 {t.reward_value} {t.reward_type === 'xp' ? 'XP' : 'BYN'}</div>
            </div>
            {t.status === 'CLAIMED' ? <span className="text-xs text-profit">✓</span> :
              t.progress_value >= t.target_value ? <button className="btn-accent text-xs !py-1.5" onClick={() => claim(t.id)}>Забрать</button> :
              <span className="text-xs text-white/40">…</span>}
          </div>
        ))}
        {!tasks.length && <div className="text-sm text-white/50">Зайдите на рынок, чтобы получить задания.</div>}
      </div>

      <div className="card">
        <div className="font-bold text-sm mb-2">🔔 События</div>
        {events.slice(0, 5).map((e) => (
          <div key={e.id} className="text-sm py-1 border-b border-white/5 last:border-0">
            <b>{e.title}</b>
            <div className="text-xs text-white/60">{e.description}</div>
          </div>
        ))}
        {!events.length && <div className="text-sm text-white/50">Пока тихо.</div>}
      </div>

      <div className="card text-sm">
        <label className="flex items-center justify-between">
          <span>Не показывать меня в рейтинге</span>
          <input type="checkbox" className="!w-6" checked={!!me?.rating_opt_out} onChange={toggleRating} />
        </label>
        <div className="text-xs text-white/40 mt-2">Игра использует виртуальную валюту. Реальных денег, ставок и выводов нет.</div>
      </div>
    </div>
  );
}

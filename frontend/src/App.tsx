import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import TopBar from './components/TopBar';
import BottomNav from './components/BottomNav';
import Market from './pages/Market';
import CarDetails from './pages/CarDetails';
import Garage from './pages/Garage';
import GarageCar from './pages/GarageCar';
import Deals from './pages/Deals';
import Leaderboard from './pages/Leaderboard';
import Profile from './pages/Profile';
import { api, setToken, getToken } from './api';
import { useStore } from './store';
import { initTelegram, getInitData } from './telegram';

export default function App() {
  const [boot, setBoot] = useState(true);
  const [err, setErr] = useState('');
  const setMe = useStore((s) => s.setMe);

  useEffect(() => {
    initTelegram();
    (async () => {
      try {
        // сначала пробуем существующий токен
        if (getToken()) {
          try {
            const me = await api.me();
            setMe(me);
            setBoot(false);
            return;
          } catch { /* токен протух — перелогин */ }
        }
        const initData = getInitData() || 'dev';
        const r = await api.auth(initData);
        setToken(r.token);
        setMe(r.user);
      } catch (e: any) {
        setErr(e.message || 'Не удалось войти');
      } finally {
        setBoot(false);
      }
    })();
  }, []);

  if (boot) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-3 bg-graphite">
        <div className="text-4xl">🚗</div>
        <div className="font-bold">Перекуп Симулятор</div>
        <div className="text-white/50 text-sm">Заводим двигатель…</div>
      </div>
    );
  }

  if (err) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-3 p-6 bg-graphite text-center">
        <div className="text-4xl">🔧</div>
        <div className="font-bold">Не удалось подключиться</div>
        <div className="text-danger text-sm">{err}</div>
        <div className="text-white/50 text-xs">Проверьте, что backend запущен и TELEGRAM_DEV_MODE=true для локального входа.</div>
        <button className="btn-accent" onClick={() => location.reload()}>Повторить</button>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-graphite max-w-md mx-auto pb-20">
        <TopBar />
        <Routes>
          <Route path="/" element={<Market />} />
          <Route path="/car/:id" element={<CarDetails />} />
          <Route path="/garage" element={<Garage />} />
          <Route path="/garage/:id" element={<GarageCar />} />
          <Route path="/deals" element={<Deals />} />
          <Route path="/rating" element={<Leaderboard />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}

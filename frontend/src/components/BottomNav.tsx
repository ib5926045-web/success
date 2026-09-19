import { NavLink } from 'react-router-dom';
import { Store, Warehouse, Handshake, Trophy, User } from 'lucide-react';

const items = [
  { to: '/', icon: Store, label: 'Рынок' },
  { to: '/garage', icon: Warehouse, label: 'Гараж' },
  { to: '/deals', icon: Handshake, label: 'Сделки' },
  { to: '/rating', icon: Trophy, label: 'Рейтинг' },
  { to: '/profile', icon: User, label: 'Профиль' },
];

export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-graphite/95 backdrop-blur border-t border-white/10 z-10">
      <div className="max-w-md mx-auto grid grid-cols-5">
        {items.map((it) => (
          <NavLink
            key={it.to}
            to={it.to}
            end={it.to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center py-2 text-[11px] ${isActive ? 'text-accent' : 'text-white/50'}`
            }
          >
            <it.icon size={22} />
            {it.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}

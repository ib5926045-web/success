import { create } from 'zustand';

interface Me {
  id: number;
  first_name?: string;
  username?: string;
  photo_url?: string;
  balance: number;
  reputation: number;
  level: number;
  experience: number;
  current_game_day: number;
  level_name: string;
  garage_limit: number;
  next_level_xp: number | null;
  total_profit: number;
  deals_count: number;
  rating_opt_out: boolean;
  season_goal: number;
  streak_days: number;
}

interface State {
  me: Me | null;
  authed: boolean;
  error: string;
  setMe: (m: Me | null) => void;
  setError: (e: string) => void;
  patchMe: (p: Partial<Me>) => void;
}

export const useStore = create<State>((set) => ({
  me: null,
  authed: false,
  error: '',
  setMe: (m) => set({ me: m, authed: !!m }),
  setError: (e) => set({ error: e }),
  patchMe: (p) => set((s) => ({ me: s.me ? { ...s.me, ...p } : s.me })),
}));

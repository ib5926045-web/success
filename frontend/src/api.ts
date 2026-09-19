const BASE = import.meta.env.VITE_API_URL || '/api';

let token = localStorage.getItem('token') || '';

export function setToken(t: string) {
  token = t;
  localStorage.setItem('token', t);
}

export function getToken() {
  return token;
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error((data as any).detail || `Ошибка ${res.status}`);
  }
  return data as T;
}

export const api = {
  auth: (initData: string) => req<{ token: string; is_new: boolean; user: any }>('/auth/telegram', {
    method: 'POST', body: JSON.stringify({ initData }),
  }),
  me: () => req<any>('/me'),
  dashboard: () => req<any>('/me/dashboard'),
  market: () => req<any>('/market'),
  refreshMarket: (advance_day: boolean) => req<any>(`/market/refresh?advance_day=${advance_day}`, { method: 'POST' }),
  car: (id: number) => req<any>(`/cars/${id}`),
  inspect: (id: number, inspection_type: string) => req<any>(`/cars/${id}/inspect`, {
    method: 'POST', body: JSON.stringify({ inspection_type }),
  }),
  negotiate: (id: number, body: any) => req<any>(`/cars/${id}/negotiate-seller`, {
    method: 'POST', body: JSON.stringify(body),
  }),
  buy: (id: number) => req<any>(`/cars/${id}/buy`, {
    method: 'POST', headers: { 'X-Idempotency-Key': crypto.randomUUID() },
  }),
  skip: (id: number) => req<any>(`/cars/${id}/skip`, { method: 'POST' }),
  garage: () => req<any[]>('/garage'),
  garageCar: (id: number) => req<any>(`/garage/${id}`),
  repair: (id: number, repair_type: string) => req<any>(`/garage/${id}/repair`, {
    method: 'POST', body: JSON.stringify({ repair_type }),
  }),
  prepare: (id: number, action: string) => req<any>(`/garage/${id}/prepare`, {
    method: 'POST', body: JSON.stringify({ action }),
  }),
  list: (id: number, body: any) => req<any>(`/garage/${id}/list`, { method: 'POST', body: JSON.stringify(body) }),
  unlist: (id: number) => req<any>(`/garage/${id}/unlist`, { method: 'POST' }),
  listings: () => req<any[]>('/listings'),
  acceptOffer: (lid: number, oid: number) => req<any>(`/listings/${lid}/offers/${oid}/accept`, {
    method: 'POST', headers: { 'X-Idempotency-Key': crypto.randomUUID() },
  }),
  declineOffer: (lid: number, oid: number) => req<any>(`/listings/${lid}/offers/${oid}/decline`, { method: 'POST' }),
  counterOffer: (lid: number, oid: number, price: number) => req<any>(`/listings/${lid}/offers/${oid}/counter`, {
    method: 'POST', body: JSON.stringify({ price }),
  }),
  history: () => req<any[]>('/deals/history'),
  events: () => req<any[]>('/events'),
  resolveEvent: (id: number) => req<any>(`/events/${id}/resolve`, { method: 'POST' }),
  tasks: () => req<any[]>('/tasks'),
  claimTask: (id: number) => req<any>(`/tasks/${id}/claim`, { method: 'POST' }),
  leaderboard: (sort = 'capital') => req<any>(`/leaderboard?sort=${sort}`),
  advisor: (car_id?: number) => req<any>(car_id ? `/advisor?car_id=${car_id}` : '/advisor'),
  patchSettings: (body: any) => req<any>('/settings', { method: 'PATCH', body: JSON.stringify(body) }),
};

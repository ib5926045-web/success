export function byn(n: number): string {
  return `${Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ')} BYN`;
}

export function carTitle(c: { brand: string; model: string; year: number; generation?: string | null }): string {
  return `${c.brand} ${c.model}${c.generation && c.generation !== '—' ? ' ' + c.generation : ''} · ${c.year}`;
}

// Детерминированный градиент аватара машины по image_seed
export function carGradient(seed: number): string {
  const palettes = [
    'from-slate-600 to-slate-900',
    'from-orange-700 to-stone-900',
    'from-blue-800 to-slate-900',
    'from-emerald-800 to-slate-900',
    'from-red-800 to-stone-900',
    'from-indigo-800 to-slate-900',
    'from-amber-700 to-stone-900',
    'from-cyan-800 to-slate-900',
  ];
  return palettes[Math.abs(seed) % palettes.length];
}

export function riskLabel(r: string): string {
  return r === 'low' ? 'Низкий риск' : r === 'medium' ? 'Средний риск' : 'Высокий риск';
}

export function riskColor(r: string): string {
  return r === 'low' ? 'bg-profit/20 text-profit' : r === 'medium' ? 'bg-accent/20 text-accent' : 'bg-danger/20 text-danger';
}

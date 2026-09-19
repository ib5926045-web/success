import { CarFront } from 'lucide-react';
import { carGradient } from '../format';

export default function CarVisual({ seed, big = false }: { seed: number; big?: boolean }) {
  return (
    <div className={`bg-gradient-to-br ${carGradient(seed)} rounded-xl flex items-center justify-center ${big ? 'h-44' : 'h-24'}`}>
      <CarFront size={big ? 90 : 52} className="text-white/80 drop-shadow-lg" strokeWidth={1.4} />
    </div>
  );
}

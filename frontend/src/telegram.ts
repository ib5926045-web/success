// Обёртка над Telegram Web Apps SDK с фолбэком для браузера
export interface TgUser {
  id?: number;
  first_name?: string;
  username?: string;
  photo_url?: string;
}

declare global {
  interface Window {
    Telegram?: any;
  }
}

export const tg = () => window.Telegram?.WebApp;

export function initTelegram() {
  const app = tg();
  if (!app) return;
  try {
    app.ready();
    app.expand();
    app.setHeaderColor?.('#16181d');
    app.setBackgroundColor?.('#16181d');
  } catch {}
}

export function getInitData(): string {
  return tg()?.initData || '';
}

export function getTgUser(): TgUser | null {
  try {
    return tg()?.initDataUnsafe?.user || null;
  } catch {
    return null;
  }
}

export function haptic(kind: 'success' | 'error' | 'select' | 'medium' | 'light' = 'select') {
  try {
    const h = tg()?.HapticFeedback;
    if (!h) return;
    if (kind === 'success' || kind === 'error') h.notificationOccurred(kind);
    else h.impactOccurred(kind === 'select' ? 'light' : kind);
  } catch {}
}

export function showBack(show: boolean, onClick?: () => void) {
  try {
    const bb = tg()?.BackButton;
    if (!bb) return;
    if (show) {
      bb.show();
      if (onClick) {
        bb.onClick(onClick);
      }
    } else {
      bb.hide();
    }
  } catch {}
}

export function mainButton(text: string, onClick: () => void, show = true) {
  try {
    const mb = tg()?.MainButton;
    if (!mb) return;
    mb.setText(text);
    mb.onClick(onClick);
    if (show) mb.show();
    else mb.hide();
  } catch {}
}

export function hideMainButton() {
  try {
    tg()?.MainButton?.hide();
  } catch {}
}

export function shareScore(text: string) {
  const url = `https://t.me/share/url?url=${encodeURIComponent('https://t.me/')}&text=${encodeURIComponent(text)}`;
  try {
    tg()?.openTelegramLink?.(url);
  } catch {
    window.open(url, '_blank');
  }
}

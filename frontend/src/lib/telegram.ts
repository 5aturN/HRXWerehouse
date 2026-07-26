/** Заглушка для запуска в обычном браузере (локальная разработка вне Telegram). */
if (!window.Telegram?.WebApp) {
  (window as any).Telegram = {
    WebApp: {
      initData: '',
      colorScheme: 'dark',
      themeParams: {},
      ready: () => {}, expand: () => {},
      showAlert: (m: string) => alert(m),
      showPopup: (p: any, cb?: (id: string) => void) => { alert(p.message); cb?.('yes'); },
      showScanQrPopup: (_p: any, cb: (d: string) => void) => {
        const raw = prompt('DEV: вставьте содержимое QR (JSON с batch_id):');
        if (raw) cb(raw);
      },
      closeScanQrPopup: () => {},
      BackButton: { show: () => {}, hide: () => {}, onClick: () => {}, offClick: () => {} },
      HapticFeedback: { impactOccurred: () => {}, notificationOccurred: () => {} },
    },
  };
}

/** Инициализация Telegram WebApp: тема, тактильная отдача. */
export const tg = window.Telegram.WebApp;

export function initTelegram() {
  tg.ready();
  tg.expand();
  // Тема подтягивается из Telegram автоматически (тёмная/светлая)
  const p = tg.themeParams;
  const root = document.documentElement.style;
  root.setProperty('--bg', p.bg_color ?? '#1e1e2e');
  root.setProperty('--bg2', p.secondary_bg_color ?? '#2a2a3c');
  root.setProperty('--text', p.text_color ?? '#e2e8f0');
  root.setProperty('--hint', p.hint_color ?? '#94a3b8');
  root.setProperty('--btn', p.button_color ?? '#3b82f6');
  root.setProperty('--btn-text', p.button_text_color ?? '#ffffff');
}

export const haptic = {
  success: () => tg.HapticFeedback.notificationOccurred('success'),
  error: () => tg.HapticFeedback.notificationOccurred('error'),
  tap: () => tg.HapticFeedback.impactOccurred('medium'),
};

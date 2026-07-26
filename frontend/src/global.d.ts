/** Минимальные типы Telegram WebApp SDK (только используемые методы). */
interface TelegramWebApp {
  initData: string;
  colorScheme: 'light' | 'dark';
  themeParams: Record<string, string>;
  ready(): void;
  expand(): void;
  showAlert(message: string, cb?: () => void): void;
  showPopup(params: {
    title?: string;
    message: string;
    buttons?: { id?: string; type?: string; text?: string }[];
  }, cb?: (id: string) => void): void;
  showScanQrPopup(params: { text?: string }, cb: (data: string) => boolean | void): void;
  closeScanQrPopup(): void;
  BackButton: {
    show(): void; hide(): void;
    onClick(cb: () => void): void; offClick(cb: () => void): void;
  };
  HapticFeedback: {
    impactOccurred(style: 'light' | 'medium' | 'heavy'): void;
    notificationOccurred(type: 'success' | 'error' | 'warning'): void;
  };
}

interface Window {
  Telegram: { WebApp: TelegramWebApp };
}

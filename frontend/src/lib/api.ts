/** API-клиент: initData прикладывается к КАЖДОМУ запросу (валидация на бэкенде). */
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': window.Telegram.WebApp.initData,
      ...(options.headers ?? {}),
    },
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({ detail: 'Сервер недоступен' }));
  if (!res.ok) throw new Error(data.detail ?? 'Ошибка сервера');
  return data as T;
}

/** Скачивание файла (Excel) с авторизацией. */
export async function apiDownload(path: string, body: unknown, filename: string) {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': window.Telegram.WebApp.initData,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('Ошибка выгрузки');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

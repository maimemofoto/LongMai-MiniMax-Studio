// Locale data lives in locales/th, alongside ComfyUI's native node translations.
// /i18n is ComfyUI's existing read-only endpoint. ComfyUI caches its locale list
// until restart when a new language folder is added.
export async function loadThaiLocale(fetcher = globalThis.fetch) {
  const response = await fetcher(new URL('/i18n', globalThis.location?.href || 'http://localhost/'), { cache: 'no-store' });
  if (!response.ok) throw new Error(`H3ZeroStudio locale HTTP ${response.status}`);
  const data = (await response.json())?.th?.H3ZeroStudio;
  if (!data || !data.ui || !Array.isArray(data.help)) throw new Error('H3ZeroStudio locales/th/main.json is missing or invalid');
  return data;
}
let locale = { ui: {}, help: [] };
if (typeof window !== 'undefined') {
  try { locale = await loadThaiLocale(); }
  catch (error) { console.warn('[H3ZeroStudio] Thai locale unavailable; using the source language.', error); }
}
export const TH = Object.freeze(locale.ui);
export const HELP_TH = locale.help;

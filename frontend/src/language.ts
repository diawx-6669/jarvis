/**
 * Language selection. English is the normal default; language can still be
 * changed by speaking an explicit command.
 */

export type Lang = "en" | "ru";

const STORAGE_KEY = "jarvis-lang";

export function getStoredLang(): Lang | null {
  const v = localStorage.getItem(STORAGE_KEY);
  return v === "en" || v === "ru" ? v : null;
}

export function setStoredLang(lang: Lang) {
  localStorage.setItem(STORAGE_KEY, lang);
}

/**
 * Detects an explicit "switch language" command from a raw transcript.
 * Works in any state, not just the first-visit modal. Returns the
 * requested language, or null if the text isn't a language-switch command.
 */
export function detectLanguageSwitch(text: string): Lang | null {
  const t = text.toLowerCase().trim();
  if (t.length > 60) return null; // long sentences are conversation, not commands

  const toRu = [
    "switch to russian", "speak russian", "talk in russian", "in russian please",
    "переключись на русский", "говори по-русски", "переключи язык на русский",
    "говори на русском", "перейди на русский",
  ];
  const toEn = [
    "switch to english", "speak english", "talk in english", "in english please",
    "переключись на английский", "говори по-английски", "переключи язык на английский",
    "говори на английском", "перейди на английский",
  ];

  if (toRu.some((p) => t.includes(p))) return "ru";
  if (toEn.some((p) => t.includes(p))) return "en";
  return null;
}

/**
 * Resolve the language to use immediately. There is deliberately no startup
 * language dialog: a fresh installation always starts in English.
 */
export function initLanguage(onChange: (lang: Lang) => void): Lang {
  const stored = getStoredLang();
  return stored ?? "en";
}

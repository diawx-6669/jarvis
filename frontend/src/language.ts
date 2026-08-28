/**
 * Language selection — first-visit modal, persisted choice.
 * Defaults to English if the user hasn't chosen yet.
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
 * Resolve the language to use immediately (default "en"), and show a
 * one-time picker modal if the user hasn't chosen before. `onChange` fires
 * whenever the user picks a language (including from the initial modal).
 */
export function initLanguage(onChange: (lang: Lang) => void): Lang {
  const stored = getStoredLang();
  const current: Lang = stored ?? "en";

  if (!stored) {
    showLanguageModal((lang) => {
      setStoredLang(lang);
      onChange(lang);
    });
  }

  return current;
}

function showLanguageModal(onSelect: (lang: Lang) => void) {
  const overlay = document.createElement("div");
  overlay.id = "lang-modal-overlay";
  overlay.innerHTML = `
    <div id="lang-modal">
      <div id="lang-modal-title">Choose your language</div>
      <div id="lang-modal-subtitle">Выберите язык</div>
      <div id="lang-modal-buttons">
        <button data-lang="en" class="lang-btn">English</button>
        <button data-lang="ru" class="lang-btn">Русский</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  overlay.querySelectorAll<HTMLButtonElement>(".lang-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const lang = (btn.dataset.lang as Lang) || "en";
      overlay.remove();
      onSelect(lang);
    });
  });
}

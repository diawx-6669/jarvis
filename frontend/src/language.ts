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

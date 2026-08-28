/**
 * JARVIS — Left Sidebar
 *
 * Collapsible panel for typing text prompts to JARVIS and switching
 * the speech-recognition language on the fly.
 */

export interface SidebarCallbacks {
  onSendText: (text: string) => void;
  onLanguageChange: (lang: string) => void;
}

const LANGUAGES: { code: string; label: string }[] = [
  { code: "en-US", label: "English" },
  { code: "ru-RU", label: "Русский" },
  { code: "es-ES", label: "Español" },
  { code: "fr-FR", label: "Français" },
  { code: "de-DE", label: "Deutsch" },
];

const STORAGE_KEY = "jarvis-lang";

let containerEl: HTMLElement | null = null;
let isOpen = false;

function buildSidebarHTML(currentLang: string): string {
  const options = LANGUAGES.map(
    (l) => `<option value="${l.code}" ${l.code === currentLang ? "selected" : ""}>${l.label}</option>`
  ).join("");

  return `
    <button class="sidebar-toggle" id="sidebar-toggle" title="Menu">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <line x1="3" y1="6" x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>
    <div class="sidebar-backdrop" id="sidebar-backdrop"></div>
    <div class="sidebar-panel" id="sidebar-panel">
      <div class="sidebar-header">
        <span>Jarvis</span>
        <button class="sidebar-close" id="sidebar-close">&times;</button>
      </div>

      <div class="sidebar-section">
        <label class="sidebar-label">Language</label>
        <select id="sidebar-lang-select">${options}</select>
      </div>

      <div class="sidebar-section sidebar-prompt-section">
        <label class="sidebar-label">Type a message</label>
        <textarea id="sidebar-prompt-input" rows="5" placeholder="Type your prompt for JARVIS..."></textarea>
        <button class="sidebar-send-btn" id="sidebar-send-btn">Send</button>
      </div>
    </div>
  `;
}

export function createSidebar(callbacks: SidebarCallbacks): void {
  const storedLang = localStorage.getItem(STORAGE_KEY) || "en-US";

  const container = document.createElement("div");
  container.id = "sidebar-container";
  container.innerHTML = buildSidebarHTML(storedLang);
  document.body.appendChild(container);
  containerEl = container;

  // Apply the stored language right away so voice recognition matches the UI
  callbacks.onLanguageChange(storedLang);

  const toggleBtn = document.getElementById("sidebar-toggle")!;
  const closeBtn = document.getElementById("sidebar-close")!;
  const backdrop = document.getElementById("sidebar-backdrop")!;
  const langSelect = document.getElementById("sidebar-lang-select") as HTMLSelectElement;
  const promptInput = document.getElementById("sidebar-prompt-input") as HTMLTextAreaElement;
  const sendBtn = document.getElementById("sidebar-send-btn")!;

  toggleBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    toggleSidebar();
  });

  closeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    closeSidebar();
  });

  backdrop.addEventListener("click", () => {
    closeSidebar();
  });

  langSelect.addEventListener("change", () => {
    const lang = langSelect.value;
    localStorage.setItem(STORAGE_KEY, lang);
    callbacks.onLanguageChange(lang);
  });

  function submitPrompt() {
    const text = promptInput.value.trim();
    if (!text) return;
    callbacks.onSendText(text);
    promptInput.value = "";
  }

  sendBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    submitPrompt();
  });

  promptInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitPrompt();
    }
  });

  // Don't let clicks inside the panel bubble up and close other dropdowns/the panel itself
  document.getElementById("sidebar-panel")!.addEventListener("click", (e) => e.stopPropagation());
}

export function toggleSidebar(): void {
  if (isOpen) closeSidebar();
  else openSidebar();
}

export function openSidebar(): void {
  if (!containerEl) return;
  isOpen = true;
  containerEl.classList.add("open");
}

export function closeSidebar(): void {
  if (!containerEl) return;
  isOpen = false;
  containerEl.classList.remove("open");
}

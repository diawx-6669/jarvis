/** A deliberately small first-run panel: enter keys once, then start talking. */

interface StatusResponse {
  env_keys_set: { groq: boolean; fish_audio: boolean; fish_voice_id: boolean };
}

let panelEl: HTMLElement | null = null;
let isOpen = false;

async function apiGet<T>(url: string): Promise<T> {
  const res = await fetch(url);
  return res.json();
}

async function apiPost<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  return res.json();
}

function buildPanelHTML(): string {
  return `
    <div class="settings-backdrop" id="settings-backdrop"></div>
    <div class="settings-panel" id="settings-panel-inner">
      <div class="settings-header"><h2>Welcome to JARVIS</h2><button class="settings-close" id="settings-close">&times;</button></div>
      <div class="settings-welcome"><p>Enter your keys once. JARVIS is ready to listen.</p></div>
      <div class="settings-body">
        <section class="settings-section" id="section-api-keys">
          <div class="settings-field"><label>Groq API Key</label><input type="password" id="input-groq-key" placeholder="gsk_..." autocomplete="off" /></div>
          <div class="settings-field"><label>Fish Audio API Key <small>(optional)</small></label><input type="password" id="input-fish-key" placeholder="Fish Audio key" autocomplete="off" /></div>
          <div class="settings-field"><label>Fish Voice ID <small>(optional)</small></label><input type="text" id="input-fish-voice-id" placeholder="Voice ID" /></div>
          <div class="settings-actions"><button class="settings-btn primary" id="btn-save-keys">Save &amp; Start</button></div>
          <p id="settings-message" class="settings-message" aria-live="polite"></p>
        </section>
      </div>
    </div>`;
}

function createPanel(): HTMLElement {
  const container = document.createElement("div");
  container.id = "settings-container";
  container.innerHTML = buildPanelHTML();
  document.body.appendChild(container);
  return container;
}

function message(text: string) {
  const el = document.getElementById("settings-message");
  if (el) el.textContent = text;
}

function wireEvents() {
  document.getElementById("settings-close")?.addEventListener("click", closeSettings);
  document.getElementById("settings-backdrop")?.addEventListener("click", closeSettings);
  document.getElementById("btn-save-keys")?.addEventListener("click", async () => {
    const entries = [
      ["GROQ_API_KEY", (document.getElementById("input-groq-key") as HTMLInputElement).value.trim()],
      ["FISH_API_KEY", (document.getElementById("input-fish-key") as HTMLInputElement).value.trim()],
      ["FISH_VOICE_ID", (document.getElementById("input-fish-voice-id") as HTMLInputElement).value.trim()],
    ];
    message("Saving…");
    try {
      await Promise.all(entries.filter(([, value]) => value).map(([key_name, key_value]) =>
        apiPost("/api/settings/keys", { key_name, key_value })
      ));
      message("Saved. Microphone permission is required the first time.");
      setTimeout(closeSettings, 900);
    } catch {
      message("Could not save the keys. Please try again.");
    }
  });
}

export async function openSettings() {
  if (isOpen) return;
  isOpen = true;
  if (!panelEl) { panelEl = createPanel(); wireEvents(); }
  panelEl.style.display = "block";
  requestAnimationFrame(() => panelEl!.classList.add("open"));
}

export function closeSettings() {
  if (!panelEl || !isOpen) return;
  isOpen = false;
  panelEl.classList.remove("open");
  setTimeout(() => { if (panelEl) panelEl.style.display = "none"; }, 300);
}

export async function checkFirstTimeSetup(): Promise<boolean> {
  try {
    const status = await apiGet<StatusResponse>("/api/settings/status");
    if (!status.env_keys_set.groq) { openSettings(); return true; }
  } catch { /* Server is still starting. */ }
  return false;
}

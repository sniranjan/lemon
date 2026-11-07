// Cookie consent for visitors in the EU/EEA, UK and Switzerland (the Worker sets
// window.__PL_CONSENT_REQUIRED in <head>). Everyone else gets analytics and session replay without a banner.
// The choice is a first-party cookie, read by the inline Google tag loader in index.html too.
import { startReplay, stopReplay } from "./replay";

declare global {
  interface Window {
    __PL_CONSENT_REQUIRED?: boolean;
    __plLoadGtm?: () => void;
  }
}

export type Consent = "granted" | "denied";
const COOKIE = "pl_consent";
export const OPEN_SETTINGS_EVENT = "pl:cookie-settings";

export const consentRequired = () => window.__PL_CONSENT_REQUIRED === true;

export function getConsent(): Consent | null {
  const m = document.cookie.match(/(?:^|; )pl_consent=(granted|denied)/);
  return m ? (m[1] as Consent) : null;
}

export const trackingAllowed = () => !consentRequired() || getConsent() === "granted";

/** Pages that show a gift code (it works like cash): analytics and replay never start here. */
export const onGiftCodePage = () => /^\/(redeem|gift\/card\/)/.test(location.pathname);

/** Leaving the site for a gift-code page mid-visit: stop the session replay so the code isn't recorded. */
export function pauseTracking() {
  stopReplay();
}

/** Start Google tag + session replay if this visitor allows it (safe to call more than once). */
export function startTracking() {
  if (!trackingAllowed() || onGiftCodePage()) return;
  window.__plLoadGtm?.();
  startReplay();
}

export function setConsent(value: Consent) {
  const before = getConsent();
  const secure = location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${COOKIE}=${value}; Max-Age=${60 * 60 * 24 * 365}; Path=/; SameSite=Lax${secure}`;
  if (value === "granted") startTracking();
  // Scripts that already started can't be unloaded; a reload leaves them off.
  else if (before === "granted") location.reload();
}

export function openCookieSettings() {
  window.dispatchEvent(new Event(OPEN_SETTINGS_EVENT));
}

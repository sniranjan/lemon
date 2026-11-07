import { useEffect, useState } from "react";
import { Cookie } from "lucide-react";
import { consentRequired, getConsent, OPEN_SETTINGS_EVENT, setConsent } from "@/lib/consent";

/** Opt-in banner, shown only to visitors in the EU/EEA, UK and Switzerland until they choose. */
export function CookieBanner() {
  const [open, setOpen] = useState(() => consentRequired() && getConsent() === null);

  useEffect(() => {
    const show = () => setOpen(true);
    window.addEventListener(OPEN_SETTINGS_EVENT, show);
    return () => window.removeEventListener(OPEN_SETTINGS_EVENT, show);
  }, []);

  if (!open) return null;
  const choose = (v: "granted" | "denied") => {
    setConsent(v);
    setOpen(false);
  };
  return (
    <div
      role="dialog"
      aria-label="Cookie choices"
      className="fixed inset-x-3 bottom-3 z-50 mx-auto max-w-2xl rounded-2xl border-[3px] border-ink bg-white p-5 shadow-[0_6px_0_0_var(--ink)] sm:bottom-5"
    >
      <div className="flex items-start gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-full border-2 border-ink bg-sun">
          <Cookie className="size-5" />
        </span>
        <div className="text-[0.95rem] leading-relaxed text-ink/85">
          <p className="text-lg font-bold text-ink">Can we use cookies?</p>
          <p className="mt-1">
            With your OK we use Google Analytics and record how the site is used (session recording, including anything
            typed on the site), so we can see what's confusing and fix it. Nothing loads until you choose. See our{" "}
            <a href="/privacy" className="font-bold text-coral underline underline-offset-2">
              privacy policy
            </a>
            ; you can change your mind any time from "Cookie settings" at the bottom of the page.
          </p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap justify-end gap-2">
        <button
          type="button"
          onClick={() => choose("denied")}
          className="rounded-full border-2 border-ink bg-white px-5 py-2 font-extrabold hover:bg-cream"
        >
          Reject all
        </button>
        <button
          type="button"
          onClick={() => choose("granted")}
          className="rounded-full border-2 border-ink bg-ink px-5 py-2 font-extrabold text-white hover:-translate-y-0.5"
        >
          Accept all
        </button>
      </div>
    </div>
  );
}

import { useEffect, useState, type ReactNode } from "react";
import { Check, Copy, Download, Gift, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { GiftSheet } from "@/components/GiftCard";
import { formatPrice, getGift, postJson, useCatalog, type GiftInfo } from "@/lib/catalog";
import { pauseTracking } from "@/lib/consent";
import { cardPdfUrl, giftFor } from "@/lib/giftShare";
import { LEVELS } from "@/data/levels";
import { cn } from "@/lib/utils";

const PRESETS = [1900, 2900, 5000];
const MESSAGE_MAX = 300;
const usd = (cents: number) => formatPrice(cents, "usd");

type Form = {
  kind: "all" | "credit";
  amount: number | "other";
  other: string;
  childName: string;
  message: string;
  buyerName: string;
};

/** /gift: the gift form. Everything is checked here and again by the Worker before Stripe Checkout. */
export function GiftPage() {
  const catalog = useCatalog();
  const gifts = catalog.gifts;
  const allCents = gifts?.allCents ?? 9900;
  const params = new URLSearchParams(location.search);
  const forLevel = LEVELS.find((l) => l.slug === params.get("for"));
  const forPrice = forLevel ? catalog.prices[forLevel.slug]?.cents : undefined;
  const levelCents = Object.values(catalog.prices)[0]?.cents;

  const [f, setF] = useState<Form>(() => ({
    kind: params.get("kind") === "credit" || forLevel ? "credit" : "all",
    amount: 1900,
    other: "",
    childName: "",
    message: "",
    buyerName: "",
  }));
  // A level card's "give as a gift": start at that level's price.
  useEffect(() => {
    if (forPrice) setF((s) => ({ ...s, amount: PRESETS.includes(forPrice) ? forPrice : "other", other: PRESETS.includes(forPrice) ? "" : String(forPrice / 100) }));
  }, [forPrice]);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ field?: string; message: string } | null>(null);
  const set = <K extends keyof Form>(k: K, v: Form[K]) => setF((s) => ({ ...s, [k]: v }));

  const amountCents = f.kind === "all" ? allCents : f.amount === "other" ? Math.round(Number(f.other) * 100) : f.amount;
  const otherOk = f.amount !== "other" || (/^\d{1,3}$/.test(f.other.trim()) && amountCents >= 1000 && amountCents <= 25000);
  const allAvailable = gifts?.allCents != null || !gifts;
  const open = Boolean(gifts?.open) && (f.kind !== "all" || gifts?.allCents != null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!otherOk) return setError({ field: "amountCents", message: "Type a whole-dollar amount from $10 to $250." });
    setBusy(true);
    setError(null);
    const d = await postJson("/api/gift/checkout", {
      kind: f.kind,
      amountCents,
      childName: f.childName,
      message: f.message,
      buyerName: f.buyerName,
    });
    if (d.ok && d.url) return window.location.assign(d.url);
    setError({ field: d.field, message: d.error ?? "Couldn't start checkout." });
    setBusy(false);
  }

  const bad = (field: string) => error?.field === field;

  return (
    <section className="px-4 py-14 sm:px-6 sm:py-20">
      <div className="mx-auto max-w-3xl">
        <div className="text-center">
          <p className="font-hand text-2xl text-coral">for birthdays and holidays</p>
          <h1 className="mt-1 text-balance text-4xl font-bold sm:text-5xl">Give paper lessons</h1>
          <p className="mx-auto mt-4 max-w-xl text-lg text-ink/80">
            A gift for another family: printable reading and math pages for kids from 3 to 12. You get a gift card
            to print or send, the moment you pay.
          </p>
        </div>

        <form onSubmit={submit} className="sticker mt-10 bg-white p-5 sm:p-8" noValidate>
          <Step n={1} title="Pick a gift">
            <div className="grid gap-4 sm:grid-cols-2">
              <Choice
                selected={f.kind === "all"}
                disabled={!allAvailable}
                onSelect={() => set("kind", "all")}
                className="bg-sun"
                badge="our favorite"
              >
                <span className="text-2xl font-bold">Every level</span>
                <span className="font-hand text-3xl text-coral">{usd(allCents)}</span>
                <span className="text-[0.95rem] font-semibold text-ink/80">
                  All 13 levels, ages 3 to 12. No need to guess their age: it grows with every child in the house.
                </span>
              </Choice>
              <Choice selected={f.kind === "credit"} onSelect={() => set("kind", "credit")} className="bg-cream">
                <span className="text-2xl font-bold">A gift amount</span>
                <span className="font-hand text-3xl text-coral">{f.amount === "other" ? (f.other ? `$${f.other}` : "$…") : usd(f.amount)}</span>
                <span className="text-[0.95rem] font-semibold text-ink/80">
                  They pick the levels.
                  {levelCents ? ` ${usd(levelCents)} buys one whole level.` : ""}
                </span>
              </Choice>
            </div>
            {f.kind === "credit" && (
              <div className="mt-4 flex flex-wrap items-center gap-2" role="radiogroup" aria-label="Gift amount">
                {PRESETS.map((c) => (
                  <Chip key={c} on={f.amount === c} onClick={() => set("amount", c)}>
                    {usd(c)}
                  </Chip>
                ))}
                <Chip on={f.amount === "other"} onClick={() => set("amount", "other")}>
                  Other
                </Chip>
                {f.amount === "other" && (
                  <label className="flex items-center gap-1 rounded-full border-[3px] border-ink bg-white px-3 py-1 font-extrabold">
                    $
                    <input
                      autoFocus
                      inputMode="numeric"
                      value={f.other}
                      onChange={(e) => set("other", e.target.value.replace(/[^\d]/g, "").slice(0, 3))}
                      placeholder="10 to 250"
                      aria-label="Gift amount in dollars, 10 to 250"
                      aria-invalid={!otherOk || bad("amountCents")}
                      className="w-24 bg-transparent outline-none"
                    />
                  </label>
                )}
                {forLevel && forPrice && amountCents === forPrice && (
                  <span className="text-sm font-bold text-ink/70">Enough for {forLevel.name}, or any level they like.</span>
                )}
              </div>
            )}
          </Step>

          <Step n={2} title="Who is it for?">
            <div className="sm:max-w-[calc(50%-0.5rem)]">
              <Field label="Child's first name" hint="Optional" error={bad("childName")}>
                <input value={f.childName} onChange={(e) => set("childName", e.target.value)} maxLength={30} autoComplete="off" placeholder="Maya" className={INPUT} />
              </Field>
            </div>
            <p className="mt-3 text-sm font-semibold text-ink/70">Just the first name, for the card. With none, it says "a gift for you".</p>
          </Step>

          <Step n={3} title="Add a message" last>
            <div className="flex flex-col gap-4">
              <Field label="Your message" hint={`Optional · ${[...f.message].length} / ${MESSAGE_MAX}`} error={bad("message")}>
                <textarea
                  value={f.message}
                  onChange={(e) => set("message", [...e.target.value].slice(0, MESSAGE_MAX).join(""))}
                  rows={4}
                  placeholder="Happy birthday, Maya! A little something for rainy afternoons."
                  className={cn(INPUT, "h-auto resize-y py-3 leading-relaxed")}
                />
              </Field>
              <div className="sm:max-w-[calc(50%-0.5rem)]">
                <Field label="From" hint="Optional · your name" error={bad("buyerName")}>
                  <input value={f.buyerName} onChange={(e) => set("buyerName", e.target.value)} maxLength={60} autoComplete="name" placeholder="Priya" className={INPUT} />
                </Field>
              </div>
            </div>
          </Step>

          <div className="mt-8 flex flex-col items-start gap-3 border-t-2 border-dashed border-ink/25 pt-6 sm:flex-row sm:items-center sm:justify-between">
            <p className="max-w-sm text-sm font-semibold text-ink/70">
              You'll get a gift card PDF to print or send, right after you pay and by email. Gift codes never expire. All sales are
              final: no refunds, no cash value. <a href="/terms#gifts" className="underline underline-offset-2">Gift terms</a>
            </p>
            <Button type="submit" variant="coral" size="pill" disabled={busy || !open} className="shrink-0">
              {busy ? <Loader2 className="size-5 animate-spin" /> : <Gift className="size-5" />}
              {open ? `Continue to payment · ${f.kind === "all" || otherOk ? usd(amountCents) : "$…"}` : "Gifts open soon"}
            </Button>
          </div>
          {error && (
            <p role="alert" className="mt-4 rounded-xl border-2 border-coral bg-coral/10 px-4 py-3 font-bold text-ink">
              {error.message}
            </p>
          )}
        </form>
      </div>
    </section>
  );
}

const INPUT =
  "h-12 w-full rounded-xl border-[3px] border-ink bg-cream px-4 text-lg font-semibold outline-none placeholder:text-ink/35 focus-visible:ring-4 focus-visible:ring-sky";

function Step({ n, title, last, children }: { n: number; title: string; last?: boolean; children: ReactNode }) {
  return (
    <fieldset className={cn("pb-7", !last && "mb-7 border-b-2 border-dashed border-ink/25")}>
      <legend className="mb-4 flex items-center gap-3 text-2xl font-bold">
        <span className="grid size-9 place-items-center rounded-full border-[3px] border-ink bg-sun text-lg">{n}</span>
        {title}
      </legend>
      {children}
    </fieldset>
  );
}

function Field({ label, hint, error, children }: { label: string; hint?: string; error?: boolean; children: ReactNode }) {
  return (
    <label className={cn("flex flex-col gap-1.5", error && "[&_input]:border-coral [&_textarea]:border-coral")}>
      <span className="flex items-baseline justify-between gap-2 font-extrabold">
        {label}
        {hint && <span className="text-sm font-semibold text-ink/60">{hint}</span>}
      </span>
      {children}
    </label>
  );
}

function Choice({
  selected,
  disabled,
  onSelect,
  className,
  badge,
  children,
}: {
  selected: boolean;
  disabled?: boolean;
  onSelect: () => void;
  className?: string;
  badge?: string;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      disabled={disabled}
      onClick={onSelect}
      className={cn(
        "relative flex cursor-pointer flex-col items-start gap-1 rounded-2xl border-[3px] border-ink p-5 text-left transition-transform hover:-translate-y-0.5 disabled:opacity-50",
        selected ? "shadow-[5px_5px_0_0_var(--ink)] ring-4 ring-sky/60" : "opacity-85",
        className,
      )}
    >
      {badge && (
        <span className="absolute -top-3 right-4 rounded-full border-2 border-ink bg-coral px-2.5 py-0.5 text-xs font-extrabold text-white">
          {badge}
        </span>
      )}
      {children}
    </button>
  );
}

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={on}
      onClick={onClick}
      className={cn(
        "inline-flex cursor-pointer items-center gap-1.5 rounded-full border-[3px] border-ink px-4 py-1.5 font-extrabold transition-transform hover:-translate-y-0.5",
        on ? "bg-ink text-white" : "bg-white",
      )}
    >
      {children}
    </button>
  );
}

/**
 * /gift/thanks?session_id=…: Stripe's return address for a gift. Waits for the gift, then shows the card and a
 * big button to download it as a PDF (the same file the buyer's email carries), and the code to copy.
 * It shows the code, so analytics stay off here (consent.ts onGiftCodePage, index.html).
 */
export function GiftThanks() {
  const [state, setState] = useState<{ kind: "loading" } | { kind: "error"; message: string } | { kind: "ready"; gift: GiftInfo }>({ kind: "loading" });
  useEffect(() => {
    pauseTracking();
    let stop = false;
    (async () => {
      const sid = new URLSearchParams(location.search).get("session_id");
      let code: string | null = null;
      for (let i = 0; !code && sid && i < 8 && !stop; i++) {
        const r = await fetch(`/api/gift/session/${encodeURIComponent(sid)}`).catch(() => null);
        const d = (await r?.json().catch(() => ({}))) as { ok?: boolean; code?: string; pending?: boolean };
        if (d?.ok && d.code) code = d.code;
        else if (d?.pending) await new Promise((res) => setTimeout(res, 1500));
        else break;
      }
      if (stop) return;
      const g = code ? await getGift(code) : null;
      setState(
        g?.ok
          ? { kind: "ready", gift: g }
          : { kind: "error", message: "We couldn't find that gift. If you were charged, email hello@paperlessons.com and we'll sort it out." },
      );
    })();
    return () => {
      stop = true;
    };
  }, []);

  return (
    <section className="px-4 py-12 sm:px-6 sm:py-20">
      {state.kind === "ready" ? (
        <GiftReady gift={state.gift} />
      ) : (
        <div className="sticker mx-auto max-w-2xl bg-white p-6 sm:p-10">
          {state.kind === "loading" ? (
            <div className="flex items-center gap-3 text-lg font-bold">
              <Loader2 className="size-6 animate-spin text-coral" /> Wrapping your gift…
            </div>
          ) : (
            <>
              <h1 className="text-3xl font-bold">Hmm, something's missing</h1>
              <p className="mt-3 text-lg text-ink/80">{state.message}</p>
            </>
          )}
        </div>
      )}
    </section>
  );
}

/** Copy to the clipboard (with an old-browser fallback); true if it worked. */
async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return ok;
  }
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const [done, setDone] = useState(false);
  return (
    <Button
      type="button"
      variant="paper"
      size="pill-sm"
      onClick={async () => {
        if (await copyText(text)) {
          setDone(true);
          setTimeout(() => setDone(false), 2000);
        }
      }}
    >
      {done ? <Check className="size-4" /> : <Copy className="size-4" />}
      <span aria-live="polite">{done ? "Copied!" : label}</span>
    </Button>
  );
}

// The card preview: the real card at full size, scaled down to fit.
const PREVIEW_W = 250;
const PREVIEW_SCALE = PREVIEW_W / 816;

function GiftReady({ gift }: { gift: GiftInfo }) {
  const forName = giftFor(gift);
  const pdf = cardPdfUrl(gift.code);

  return (
    <div className="mx-auto max-w-3xl">
      <div className="text-center">
        <p className="font-hand text-2xl text-coral">thank you!</p>
        <h1 className="text-balance text-3xl font-bold leading-tight sm:text-4xl">Your gift card is ready</h1>
        <p className="mx-auto mt-3 max-w-xl text-lg text-ink/80">
          {forName ? `Print it for ${forName}, ` : "Print it "}
          or send the PDF on by email or text.
        </p>
      </div>

      <div className="sticker mt-8 grid items-center gap-6 bg-white p-5 sm:grid-cols-[auto_1fr] sm:gap-8 sm:p-8">
        <a
          href={pdf}
          aria-label="Download the gift card (PDF)"
          className="mx-auto block overflow-hidden rounded-[0.6rem] transition-transform hover:-translate-y-0.5"
          style={{ width: PREVIEW_W + 4, height: 1056 * PREVIEW_SCALE + 4 }}
        >
          <div aria-hidden="true" style={{ width: 816, transform: `scale(${PREVIEW_SCALE})`, transformOrigin: "top left" }}>
            <GiftSheet gift={gift} fixed />
          </div>
        </a>

        <div className="flex min-w-0 flex-col gap-6">
          <Button asChild variant="coral" size="pill" className="w-full sm:w-auto sm:self-start">
            <a href={pdf} download>
              <Download className="size-5" /> Download gift card (PDF)
            </a>
          </Button>

          <div className="rounded-2xl border-[3px] border-dashed border-ink bg-cream p-5 text-center">
            <p className="text-sm font-extrabold uppercase tracking-wide text-ink/60">Gift code</p>
            <p className="mt-1 font-display text-[1.5rem] font-bold leading-tight tracking-[0.08em] whitespace-nowrap min-[400px]:text-[1.75rem] sm:text-[2rem] sm:tracking-[0.1em]">{gift.code}</p>
            <div className="mt-3 flex justify-center">
              <CopyButton text={gift.code} label="Copy code" />
            </div>
            <p className="mt-3 text-sm font-semibold text-ink/65">They open it at paperlessons.com/redeem. It never expires.</p>
          </div>

          <p className="font-semibold text-ink/75">We've emailed it to you too, with your receipt.</p>

          <a href="/gift" className="inline-flex items-center gap-1.5 self-start font-extrabold text-ink/80 underline-offset-4 hover:text-coral hover:underline">
            <Sparkles className="size-4 text-coral" /> Give another
          </a>
        </div>
      </div>
    </div>
  );
}

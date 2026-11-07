import { useEffect, useState } from "react";
import { pauseTracking } from "@/lib/consent";
import { Check, Gift, Loader2, Mail, ShoppingBag } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatPrice, getGift, longDate, postJson, useCatalog, type GiftInfo } from "@/lib/catalog";
import { planPayment, quoteCart } from "@/lib/cart";
import { LEVELS } from "@/data/levels";
import { cn } from "@/lib/utils";

const usd = (cents: number) => formatPrice(cents, "usd");
const INPUT =
  "h-12 w-full rounded-xl border-[3px] border-ink bg-cream px-4 text-lg font-semibold outline-none placeholder:text-ink/35 focus-visible:ring-4 focus-visible:ring-sky";

/**
 * /redeem (or /redeem?code=…, the link in the gift email): type a code, see the gift, open it.
 * Every-level gifts open with one click; a gift amount shops the library with the balance applied.
 */
export function RedeemPage() {
  // The code arrives as ?code= (email link, a fresh page load with no analytics) or #CODE; it is kept in the
  // fragment afterwards, which analytics page views leave out.
  const [typed, setTyped] = useState(
    () => new URLSearchParams(location.search).get("code") ?? decodeURIComponent(location.hash.slice(1)),
  );
  const [gift, setGift] = useState<GiftInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(code: string) {
    if (!code.trim()) return;
    setLoading(true);
    setError(null);
    const g = await getGift(code.trim());
    setLoading(false);
    if (g.ok) {
      setGift(g);
      history.replaceState(null, "", `/redeem#${g.code}`);
    } else setError(g.error);
  }

  useEffect(() => {
    pauseTracking();
    if (typed) load(typed);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section className="px-4 py-14 sm:px-6 sm:py-20">
      <div className="mx-auto max-w-3xl">
        {!gift ? (
          <div className="sticker mx-auto max-w-xl bg-white p-6 sm:p-10">
            <p className="font-hand text-2xl text-coral">someone sent you a gift</p>
            <h1 className="text-3xl font-bold sm:text-4xl">Open your gift</h1>
            <p className="mt-3 text-lg text-ink/80">Type the code from your gift card or email. Codes never expire.</p>
            <form
              className="mt-6 flex flex-col gap-3 sm:flex-row"
              onSubmit={(e) => {
                e.preventDefault();
                load(typed);
              }}
            >
              <input
                value={typed}
                onChange={(e) => setTyped(e.target.value.toUpperCase())}
                placeholder="ABCD-EFGH-JKMN"
                aria-label="Gift code"
                autoCapitalize="characters"
                autoComplete="off"
                spellCheck={false}
                className={cn(INPUT, "font-display text-xl tracking-[0.12em]")}
              />
              <Button type="submit" variant="coral" size="pill" disabled={loading} className="shrink-0">
                {loading ? <Loader2 className="size-5 animate-spin" /> : <Gift className="size-5" />} Open
              </Button>
            </form>
            {error && (
              <p role="alert" className="mt-4 font-bold text-coral">
                {error}
              </p>
            )}
          </div>
        ) : (
          <GiftView gift={gift} reload={() => load(gift.code)} />
        )}
      </div>
    </section>
  );
}

function GiftView({ gift, reload }: { gift: GiftInfo; reload: () => void }) {
  return (
    <>
      <div className="sticker relative bg-sun p-6 sm:p-8">
        <p className="font-hand text-2xl text-coral">a gift for {gift.recipientName || "you"}</p>
        <h1 className="text-3xl font-bold leading-tight sm:text-4xl">
          {gift.kind === "all" ? "Every level, ages 3 to 12" : `${usd(gift.amountCents)} to spend on any level`}
        </h1>
        {gift.buyerName && <p className="mt-1 text-lg font-bold">from {gift.buyerName}</p>}
        {gift.message && (
          <blockquote className="mt-4 rounded-2xl border-[3px] border-ink bg-white px-5 py-4 text-lg leading-relaxed whitespace-pre-line">
            {gift.message}
          </blockquote>
        )}
      </div>

      {gift.kind === "all" ? <OpenAll gift={gift} /> : <Shop gift={gift} reload={reload} />}

      {gift.orders.length > 0 && <Orders gift={gift} />}
    </>
  );
}

function EmailField({ email, setEmail }: { email: string; setEmail: (v: string) => void }) {
  return (
    <label className="mt-5 flex flex-col gap-1.5">
      <span className="flex items-baseline justify-between gap-2 font-extrabold">
        Your email <span className="text-sm font-semibold text-ink/60">We send your download link here.</span>
      </span>
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" placeholder="you@example.com" className={INPUT} />
    </label>
  );
}

/** Every-level gift: one click turns it into an order for all 13 levels. */
function OpenAll({ gift }: { gift: GiftInfo }) {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (gift.redeemed) {
    return (
      <div className="sticker mt-8 bg-white p-6 sm:p-8">
        <h2 className="text-2xl font-bold">This gift has been opened</h2>
        <p className="mt-2 text-lg text-ink/80">All 13 levels went to the email used when it was opened. Need the link again? Resend it below.</p>
      </div>
    );
  }
  return (
    <form
      className="sticker mt-8 bg-white p-6 sm:p-8"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        setError(null);
        const d = await postJson(`/api/gift/${gift.code}/redeem`, { email });
        if (d.ok && d.token) return window.location.assign(`/orders/${d.token}`);
        setError(d.error ?? "Couldn't open the gift.");
        setBusy(false);
      }}
    >
      <h2 className="text-2xl font-bold">All 13 levels, Chicks to Whales</h2>
      <p className="mt-2 text-lg text-ink/80">
        Reading and math for ages 3 to 12, with answer keys. Open it once and you get one download page for every level.
      </p>
      <EmailField email={email} setEmail={setEmail} />
      <Button type="submit" variant="coral" size="pill" disabled={busy} className="mt-5">
        {busy ? <Loader2 className="size-5 animate-spin" /> : <Gift className="size-5" />} Open my gift
      </Button>
      <p className="mt-3 text-sm font-semibold text-ink/65">Your download link works for 7 days, so save the files when they arrive.</p>
      {error && (
        <p role="alert" className="mt-3 font-bold text-coral">
          {error}
        </p>
      )}
    </form>
  );
}

/** Gift amount: pick levels, see the balance come off, pay the rest (or nothing). */
function Shop({ gift, reload }: { gift: GiftInfo; reload: () => void }) {
  const catalog = useCatalog();
  const [picked, setPicked] = useState<string[]>([]);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const forSale = LEVELS.filter((l) => catalog.forSale.includes(l.slug));
  const quote = quoteCart(picked, catalog);
  const plan = quote ? planPayment(quote.cents, gift.balanceCents) : null;
  const toggle = (slug: string) => setPicked((p) => (p.includes(slug) ? p.filter((s) => s !== slug) : [...p, slug]));

  if (gift.balanceCents <= 0) {
    return (
      <div className="sticker mt-8 bg-white p-6 sm:p-8">
        <h2 className="text-2xl font-bold">This gift is all used up</h2>
        <p className="mt-2 text-lg text-ink/80">
          Every dollar has gone to levels. Need a download link again? Resend it below.
        </p>
      </div>
    );
  }

  return (
    <form
      className="sticker mt-8 bg-white p-6 sm:p-8"
      onSubmit={async (e) => {
        e.preventDefault();
        if (!quote) return setError("Pick at least one level.");
        setBusy(true);
        setError(null);
        const d = await postJson(`/api/gift/${gift.code}/checkout`, { levels: quote.slugs, email });
        if (d.ok && d.url) return window.location.assign(d.url);
        if (d.ok && d.token) return window.location.assign(`/orders/${d.token}`);
        setError(d.error ?? "Couldn't start checkout.");
        setBusy(false);
        reload();
      }}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-2xl font-bold">Pick your levels</h2>
        <p className="rounded-full border-[3px] border-ink bg-leaf/30 px-4 py-1 text-lg font-extrabold">Balance {usd(gift.balanceCents)}</p>
      </div>
      {!forSale.length ? (
        <p className="mt-4 rounded-xl border-2 border-dashed border-ink/50 p-4 font-bold">
          The shop is getting ready. Your balance is safe on this code: come back soon.
        </p>
      ) : (
        <ul className="mt-5 grid gap-3 sm:grid-cols-2">
          {forSale.map((l) => {
            const on = picked.includes(l.slug) || quote?.kind === "all";
            const price = catalog.prices[l.slug];
            return (
              <li key={l.slug}>
                <button
                  type="button"
                  aria-pressed={on}
                  onClick={() => toggle(l.slug)}
                  className={cn(
                    "flex w-full cursor-pointer items-center gap-3 rounded-2xl border-[3px] border-ink p-3 text-left transition-transform hover:-translate-y-0.5",
                    on ? "bg-sun shadow-[4px_4px_0_0_var(--ink)]" : "bg-cream",
                  )}
                >
                  <img src={l.mascot} alt="" className="size-12 shrink-0 rounded-full border-[3px] border-ink bg-white p-1" />
                  <span className="flex-1">
                    <span className="block text-lg font-bold leading-tight">{l.name}</span>
                    <span className="text-sm font-semibold text-ink/70">Age {l.age} · {l.title}</span>
                  </span>
                  <span className="shrink-0 font-extrabold">{price && usd(price.cents)}</span>
                  <span className={cn("grid size-7 shrink-0 place-items-center rounded-full border-[3px] border-ink", on ? "bg-ink text-white" : "bg-white")}>
                    {on && <Check className="size-4" />}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      {quote && plan && (
        <div className="mt-6 rounded-2xl border-[3px] border-ink bg-cream p-4 text-lg">
          {quote.kind === "all" && <p className="mb-2 font-bold text-coral">That's every level, for the every-level price.</p>}
          {quote.kind === "two" && <p className="mb-2 font-bold text-coral">Two levels in a row: the two-level pack price.</p>}
          <Row label={quote.kind === "all" ? `Every level (${quote.slugs.length})` : `${quote.slugs.length} level${quote.slugs.length > 1 ? "s" : ""}`} value={usd(quote.cents)} />
          <Row label="From your gift" value={`−${usd(plan.use)}`} />
          <div className="my-2 border-t-2 border-dashed border-ink/30" />
          <Row label={plan.rest ? "To pay" : "To pay: nothing!"} value={usd(plan.rest)} bold />
          {gift.balanceCents - plan.use > 0 && (
            <p className="mt-1 text-sm font-semibold text-ink/65">{usd(gift.balanceCents - plan.use)} stays on your code for later.</p>
          )}
        </div>
      )}

      {gift.heldCents > 0 && (
        <p className="mt-4 text-sm font-semibold text-ink/70">
          You have a checkout open for this gift. Starting a new one here closes it, so nothing is paid twice.
        </p>
      )}
      {forSale.length > 0 && <EmailField email={email} setEmail={setEmail} />}
      {forSale.length > 0 && (
        <Button type="submit" variant="coral" size="pill" disabled={busy || !quote} className="mt-5">
          {busy ? <Loader2 className="size-5 animate-spin" /> : <ShoppingBag className="size-5" />}
          {plan && plan.rest > 0 ? `Pay the rest · ${usd(plan.rest)}` : "Get my pages"}
        </Button>
      )}
      <p className="mt-3 text-sm font-semibold text-ink/65">
        {plan && plan.rest > 0
          ? "You'll pay the rest on our secure checkout. The gift is only used once the payment goes through."
          : "Your download link works for 7 days, so save the files when they arrive."}
      </p>
      {error && (
        <p role="alert" className="mt-3 font-bold text-coral">
          {error}
        </p>
      )}
    </form>
  );
}

function Row({ label, value, bold }: { label: string; value: string; bold?: boolean }) {
  return (
    <p className={cn("flex justify-between gap-4", bold ? "text-xl font-extrabold" : "font-semibold")}>
      <span>{label}</span>
      <span>{value}</span>
    </p>
  );
}

/** What this code has bought, with "Resend my files" (the same 7-day links, emailed again). */
function Orders({ gift }: { gift: GiftInfo }) {
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  const anyLive = gift.orders.some((o) => !o.expired);
  return (
    <div className="sticker mt-8 bg-white p-6 sm:p-8">
      <h2 className="text-2xl font-bold">Opened with this gift</h2>
      <ul className="mt-3 flex flex-col gap-2">
        {gift.orders.map((o, i) => (
          <li key={i} className="flex flex-wrap items-baseline justify-between gap-2 rounded-xl border-2 border-ink/20 bg-cream px-4 py-2">
            <span className="font-bold">{o.name}</span>
            <span className="text-sm font-semibold text-ink/65">
              {longDate(o.createdAt)} · {o.expired ? "link expired" : `link works until ${longDate(o.expiresAt)}`}
            </span>
          </li>
        ))}
      </ul>
      <Button
        type="button"
        variant="paper"
        size="pill-sm"
        disabled={busy || !anyLive}
        className="mt-4"
        onClick={async () => {
          setBusy(true);
          const d = await postJson(`/api/gift/${gift.code}/resend`, {});
          setNote(d.ok ? { ok: true, text: "Sent! Check the inbox you used (and the spam folder)." } : { ok: false, text: d.error ?? "Couldn't resend." });
          setBusy(false);
        }}
      >
        {busy ? <Loader2 className="size-4 animate-spin" /> : <Mail className="size-4" />} Resend my files
      </Button>
      <p className="mt-2 text-sm font-semibold text-ink/65">
        {anyLive ? "We email the download link again to the address it was sent to." : "Download links last 7 days after opening, and these have expired."}
      </p>
      {note && (
        <p role="status" className={cn("mt-2 font-bold", note.ok ? "text-teal" : "text-coral")}>
          {note.text}
        </p>
      )}
    </div>
  );
}

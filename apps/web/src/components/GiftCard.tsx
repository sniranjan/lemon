import { useEffect, useState } from "react";
import { pauseTracking } from "@/lib/consent";
import { Download, Gift, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LogoMark } from "@/components/Logo";
import { formatPrice, getGift, type GiftInfo } from "@/lib/catalog";
import { cardPdfUrl, giftFor } from "@/lib/giftShare";
import { LEVELS } from "@/data/levels";
import { cn } from "@/lib/utils";

// A few mascots along the bottom of the card, from the first rung to the last.
const MASCOTS = ["chicks", "bunnies", "foxes", "owls", "pandas", "whales"]
  .map((s) => LEVELS.find((l) => l.slug === s)?.mascot)
  .filter(Boolean) as string[];

/**
 * /gift/card/<code>: the gift card on screen, in our paper style, with an "Open your gift" button (→ /redeem#CODE)
 * and the same card as a PDF to download (worker/giftCard.ts draws it). Printing the page still prints just the
 * sheet (the site's header and footer and the greeting are hidden).
 */
export function GiftCard({ code }: { code: string }) {
  const [gift, setGift] = useState<GiftInfo | null | "missing">(null);
  useEffect(() => {
    pauseTracking();
    getGift(code).then((g) => setGift(g.ok ? g : "missing"));
  }, [code]);

  if (gift === null) {
    return (
      <div className="flex items-center justify-center gap-3 py-24 text-lg font-bold">
        <Loader2 className="size-6 animate-spin text-coral" /> Finding the gift card…
      </div>
    );
  }
  if (gift === "missing") {
    return (
      <section className="px-4 py-24 text-center">
        <h1 className="text-3xl font-bold">We couldn't find that gift card</h1>
        <p className="mt-3 text-lg text-ink/80">Check the link you were sent, or write to hello@paperlessons.com.</p>
      </section>
    );
  }

  const forName = giftFor(gift);
  return (
    <section className="gift-card-page px-4 py-10 print:p-0">
      <div className="sticker mx-auto mb-6 flex max-w-[816px] flex-col gap-4 bg-sun p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6 print:hidden">
        <div>
          <p className="font-hand text-2xl leading-none text-coral">{forName ? `hi ${forName}!` : "hello!"}</p>
          <p className="mt-1 text-xl font-bold leading-snug">
            {gift.buyerName ? `${gift.buyerName} sent you a gift.` : "Someone sent you a gift."} It's ready when you are.
          </p>
        </div>
        <Button asChild variant="coral" size="pill" className="shrink-0">
          <a href={`/redeem#${gift.code}`}>
            <Gift className="size-5" /> Open your gift
          </a>
        </Button>
      </div>

      <div className="mx-auto mb-4 flex max-w-[816px] flex-wrap items-center justify-between gap-3 print:hidden">
        <p className="font-semibold text-ink/75">Want it on paper? Download the card and print it.</p>
        <Button asChild variant="paper" size="pill">
          <a href={cardPdfUrl(gift.code)} download>
            <Download className="size-5" /> Download gift card (PDF)
          </a>
        </Button>
      </div>

      <GiftSheet gift={gift} />
    </section>
  );
}

/**
 * The card itself. `fixed` draws it at its full 816 × 1056 size whatever the screen (for the scaled-down preview
 * on the thanks page); otherwise it is fluid on screen and exactly one Letter page in print.
 */
export function GiftSheet({ gift, fixed }: { gift: GiftInfo; fixed?: boolean }) {
  // Long names and messages get smaller type, so the card always stays on one page.
  // "a gift for Maya" (an older gift's grown-up name stands in); "you" with no name.
  const forName = giftFor(gift) ?? "you";
  const nameLen = forName.length;
  const nameSize = nameLen > 34 ? "text-[2.35rem]" : nameLen > 20 ? "text-[2.9rem]" : "text-[3.6rem]";
  const long = nameLen > 20 || (gift.message?.length ?? 0) > 160;
  const buyer = gift.buyerName;
  const what = gift.kind === "all" ? "Every level, ages 3 to 12" : `${formatPrice(gift.amountCents, gift.currency)} to spend on any level`;
  const detail =
    gift.kind === "all"
      ? "All 13 levels of printable reading and math pages, from first words and counting to fractions and algebra."
      : "Printable reading and math pages for ages 3 to 12, from first words and counting to fractions and algebra.";

  return (
    <article
      aria-label={`Gift card for ${forName}`}
      className={cn(
        "gift-sheet relative mx-auto flex flex-col overflow-hidden rounded-[1.5rem] border-[3px] border-ink bg-white px-[7%] py-[7%] shadow-[6px_6px_0_0_var(--ink)] print:rounded-none print:border-0 print:shadow-none",
        fixed ? "h-[1056px] w-[816px]" : "w-full max-w-[816px] sm:aspect-[8.5/11]",
      )}
    >
      {/* paper decorations */}
      <div aria-hidden="true" className="pointer-events-none absolute -right-16 -top-16 size-64 rounded-full bg-sun" />
      <div aria-hidden="true" className="pointer-events-none absolute -bottom-20 -left-20 size-72 rounded-full bg-sky/25" />

      <header className="relative flex items-center gap-3">
        <LogoMark className="size-14" />
        <span className="text-[2.6rem] leading-none whitespace-nowrap">
          <span className="font-display font-bold tracking-tight text-ink">paper</span>
          <span className="inline-block -rotate-3 translate-y-0.5 font-hand text-[1.12em] text-coral">lessons</span>
        </span>
      </header>

      <div className={cn("relative", long ? "mt-[5%]" : "mt-[9%]")}>
        <p className="font-hand text-[2rem] text-coral">a gift for</p>
        <h1 className={cn("text-balance font-display font-bold leading-[1.02]", nameSize)}>{forName}</h1>
        {buyer && <p className={cn("mt-3 font-bold", buyer.length > 30 ? "text-[1.2rem]" : "text-[1.45rem]")}>from {buyer}</p>}
      </div>

      {gift.message ? (
        <blockquote
          className={cn(
            "relative mt-[4%] max-w-[88%] -rotate-1 rounded-2xl border-[3px] border-ink bg-cream px-6 py-4 whitespace-pre-line",
            gift.message.length > 160 ? "text-[1.05rem] leading-normal" : "text-[1.3rem] leading-relaxed",
          )}
        >
          {gift.message}
        </blockquote>
      ) : (
        // No message: our own little note, so the card never looks empty.
        <p className="relative mt-[5%] max-w-[80%] -rotate-1 font-hand text-[2.1rem] leading-tight text-ink/80">
          little lessons, one page at a time: to read, count and grow with, a few pages a day.
        </p>
      )}

      <div className={cn("relative", fixed ? "mt-auto" : "mt-10 sm:mt-auto")}>
        <p className="text-[1.6rem] font-bold leading-tight">{what}</p>
        <p className="mt-1 max-w-[80%] text-[1.05rem] font-semibold text-ink/75">{detail}</p>

        <div className={cn("mt-5 rounded-2xl border-[3px] border-dashed border-ink bg-white py-4", fixed ? "px-6" : "px-4 sm:px-6")}>
          <p className="text-sm font-extrabold uppercase tracking-[0.15em] text-ink/60">Your gift code</p>
          <p className={cn("mt-1 font-display font-bold leading-none whitespace-nowrap", fixed ? "text-[2.7rem] tracking-[0.14em]" : "text-[1.4rem] tracking-[0.06em] min-[400px]:text-[1.75rem] min-[400px]:tracking-[0.08em] sm:text-[2.7rem] sm:tracking-[0.14em]")}>{gift.code}</p>
          <p className="mt-3 text-[1.15rem] font-bold">
            Open it at <span className="text-coral">paperlessons.com/redeem</span>
          </p>
          <p className="text-[0.95rem] font-semibold text-ink/65">The code never expires. Open it whenever you're ready.</p>
        </div>

        <div aria-hidden="true" className={cn("mt-5 flex items-end", fixed ? "gap-3" : "gap-2 sm:gap-3")}>
          {MASCOTS.map((m, i) => (
            <img key={m} src={m} alt="" className={cn(fixed ? "size-12" : "size-9 min-[400px]:size-10 sm:size-12", "rounded-full border-[3px] border-ink bg-white p-1")} style={{ transform: `rotate(${i % 2 ? 6 : -6}deg)` }} />
          ))}
        </div>
      </div>
    </article>
  );
}

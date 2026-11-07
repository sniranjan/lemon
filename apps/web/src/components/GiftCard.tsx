import { useEffect, useState } from "react";
import { pauseTracking } from "@/lib/consent";
import { Loader2, Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LogoMark } from "@/components/Logo";
import { formatPrice, getGift, type GiftInfo } from "@/lib/catalog";
import { LEVELS } from "@/data/levels";
import { cn } from "@/lib/utils";

// A few mascots along the bottom of the card, from the first rung to the last.
const MASCOTS = ["chicks", "bunnies", "foxes", "owls", "pandas", "whales"]
  .map((s) => LEVELS.find((l) => l.slug === s)?.mascot)
  .filter(Boolean) as string[];

/**
 * /gift/card/<code>: the printable gift card, one US Letter page in our paper style. On screen it shows as a
 * sheet with a Print button; in print only the sheet is printed (the site's header and footer are hidden).
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
        <p className="mt-3 text-lg text-ink/80">Check the link in your email, or write to hello@paperlessons.com.</p>
      </section>
    );
  }

  // Long names and messages get smaller type, so the card always stays on one page.
  // The child's name leads when there is one ("a gift for Maya"); the grown-up's name otherwise.
  const forName = gift.childName || gift.recipientName;
  const nameLen = forName.length;
  const nameSize = nameLen > 34 ? "text-[2.35rem]" : nameLen > 20 ? "text-[2.9rem]" : "text-[3.6rem]";
  const long = nameLen > 20 || (gift.message?.length ?? 0) > 160;
  const what = gift.kind === "all" ? "Every level, ages 3 to 12" : `${formatPrice(gift.amountCents, gift.currency)} to spend on any level`;
  const detail =
    gift.kind === "all"
      ? "All 13 levels of printable reading and math pages, from first words and counting to fractions and algebra."
      : "Printable reading and math pages for ages 3 to 12, from first words and counting to fractions and algebra.";

  return (
    <section className="gift-card-page px-4 py-10 print:p-0">
      <div className="mx-auto mb-6 flex max-w-[816px] flex-wrap items-center justify-between gap-3 print:hidden">
        <p className="text-lg font-semibold text-ink/80">Print it on plain paper, then fold it or tuck it into a card.</p>
        <Button variant="coral" size="pill" onClick={() => window.print()}>
          <Printer className="size-5" /> Print
        </Button>
      </div>

      <article
        aria-label={`Gift card for ${gift.recipientName}`}
        className="gift-sheet relative mx-auto flex w-full sm:aspect-[8.5/11] max-w-[816px] flex-col overflow-hidden rounded-[1.5rem] border-[3px] border-ink bg-white px-[7%] py-[7%] shadow-[6px_6px_0_0_var(--ink)] print:rounded-none print:border-0 print:shadow-none"
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
          <h1 className={cn("text-balance font-display font-bold leading-[1.02]", nameSize)}>
            {forName}
          </h1>
          <p className={cn("mt-3 font-bold", gift.buyerName.length > 30 ? "text-[1.2rem]" : "text-[1.45rem]")}>from {gift.buyerName}</p>
        </div>

        {gift.message && (
          <blockquote
            className={cn(
              "relative mt-[4%] max-w-[88%] -rotate-1 rounded-2xl border-[3px] border-ink bg-cream px-6 py-4 whitespace-pre-line",
              gift.message.length > 160 ? "text-[1.05rem] leading-normal" : "text-[1.3rem] leading-relaxed",
            )}
          >
            {gift.message}
          </blockquote>
        )}

        <div className="relative mt-10 sm:mt-auto">
          <p className="text-[1.6rem] font-bold leading-tight">{what}</p>
          <p className="mt-1 max-w-[80%] text-[1.05rem] font-semibold text-ink/75">{detail}</p>

          <div className="mt-5 rounded-2xl border-[3px] border-dashed border-ink bg-white px-6 py-4">
            <p className="text-sm font-extrabold uppercase tracking-[0.15em] text-ink/60">Your gift code</p>
            <p className="mt-1 font-display text-[2.7rem] font-bold leading-none tracking-[0.14em]">{gift.code}</p>
            <p className="mt-3 text-[1.15rem] font-bold">
              Open it at <span className="text-coral">paperlessons.com/redeem</span>
            </p>
            <p className="text-[0.95rem] font-semibold text-ink/65">The code never expires. Open it whenever you're ready.</p>
          </div>

          <div aria-hidden="true" className="mt-5 flex items-end gap-3">
            {MASCOTS.map((m, i) => (
              <img key={m} src={m} alt="" className="size-12 rounded-full border-[3px] border-ink bg-white p-1" style={{ transform: `rotate(${(i % 2 ? 6 : -6)}deg)` }} />
            ))}
          </div>
        </div>
      </article>
    </section>
  );
}

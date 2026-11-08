import { useEffect, useRef, useState } from "react";
import { Download, Gift, Loader2, ShoppingBag, Sparkles } from "lucide-react";
import { formatPrice, startCheckout, useCatalog, type Catalog } from "@/lib/catalog";
import { gradeLabel, LEVELS, SUBJECT_LABEL, type Level } from "@/data/levels";
import { SheetPreview } from "@/components/SheetPreview";
import { SectionHeading } from "@/components/SectionHeading";
import { cn } from "@/lib/utils";

const BG: Record<Level["color"], string> = {
  sun: "bg-sun",
  coral: "bg-coral",
  teal: "bg-teal",
  sky: "bg-sky",
  grape: "bg-grape",
  leaf: "bg-leaf",
};

export function Library() {
  const catalog = useCatalog();
  return (
    <section id="library" className="scroll-mt-24 px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <SectionHeading eyebrow="the library" title="Thirteen levels, one big climb">
          Every level has reading and math, from age 3 to 12, and the work runs about two grades ahead of school.
          <span className="hidden sm:inline"> Hover a level to peek at a sheet.</span>
          <span className="sm:hidden"> Tap a level to peek at a sheet.</span>
        </SectionHeading>
        <div className="mt-12 grid gap-7 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {LEVELS.map((level, i) => (
            <LevelCard key={level.slug} level={level} index={i} catalog={catalog} />
          ))}
        </div>
        {catalog.bundles.all && <EverythingBundle catalog={catalog} />}
      </div>
    </section>
  );
}

/** One price for every level on sale (the "all" bundle). */
function EverythingBundle({ catalog }: { catalog: Catalog }) {
  const all = catalog.bundles.all!;
  const separately = catalog.forSale.reduce((sum, s) => sum + (catalog.prices[s]?.cents ?? 0), 0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="sticker relative mx-auto mt-14 flex max-w-4xl flex-col items-center gap-5 bg-sun px-6 py-8 text-center sm:flex-row sm:text-left">
      <div className="flex-1">
        <p className="font-hand text-2xl text-coral">the whole climb</p>
        <h3 className="mt-1 text-3xl font-bold leading-tight">Every level, ages 3 to 12</h3>
        <p className="mt-2 text-lg text-ink/80">
          All {all.levels} levels in one go, for brothers and sisters or a whole school year and beyond.
          {separately > all.cents && <> That's {formatPrice(separately, all.currency)} if bought one at a time.</>}
        </p>
      </div>
      <button
        type="button"
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          setError(await startCheckout(null, "all"));
          setBusy(false);
        }}
        className={cn(FLOAT, "inline-flex shrink-0 items-center gap-2 bg-white px-6 py-3 text-lg disabled:opacity-70")}
      >
        {busy ? <Loader2 className="size-5 animate-spin" /> : <ShoppingBag className="size-5" />} Get all {all.levels} ·{" "}
        {formatPrice(all.cents, all.currency)}
      </button>
      <a href="/gift?kind=all" className={cn(FLOAT, "inline-flex shrink-0 items-center gap-2 bg-coral px-6 py-3 text-lg text-white")}>
        <Gift className="size-5" /> Give as a gift
      </a>
      {error && (
        <p role="alert" className="w-full text-sm font-bold text-coral sm:absolute sm:-bottom-8 sm:left-6">
          {error}
        </p>
      )}
    </div>
  );
}

function LevelCard({ level, index, catalog }: { level: Level; index: number; catalog: Catalog }) {
  // A link to /#<slug> (e.g. from a Pinterest pin) lands on this card, opened.
  const linked = typeof location !== "undefined" && location.hash === `#${level.slug}`;
  const [open, setOpen] = useState(linked);
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    if (linked) ref.current?.scrollIntoView({ block: "center" });
  }, [linked]);
  const hasPreview = catalog.previews.includes(level.slug);
  const price = catalog.forSale.includes(level.slug) ? catalog.prices[level.slug] : undefined;
  const nextSlug = price ? catalog.next[level.slug] : undefined;
  const pack = nextSlug && catalog.bundles.two ? catalog.bundles.two : undefined;
  const nextName = nextSlug ? LEVELS.find((l) => l.slug === nextSlug)?.name : undefined;
  const ready = level.status === "ready";
  return (
    <article
      ref={ref}
      id={level.slug}
      data-open={open}
      onClick={() => setOpen((o) => !o)}
      onKeyDown={(e) => {
        if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault();
          setOpen((o) => !o);
        }
      }}
      tabIndex={0}
      aria-label={`${level.name}: ${level.blurb}`}
      className="card-rise sticker group relative h-[450px] scroll-mt-28 cursor-pointer overflow-hidden bg-cream outline-none transition-transform duration-300 hover:-translate-y-1 focus-visible:ring-4 focus-visible:ring-sky motion-reduce:transition-none"
      style={{ animationDelay: `${index * 70}ms` }}
    >
      {/* The sheet, tucked into the pocket. */}
      <div
        className="absolute inset-x-5 top-5 h-[318px] origin-bottom -rotate-2 transition-transform duration-500 ease-[cubic-bezier(.2,.9,.3,1.2)] peek:rotate-0 peek:scale-[1.02] motion-reduce:transition-none"
      >
        <SheetPreview level={level} className="h-full" />
      </div>

      {/* While peeking, the buttons float on the sheet so they're easy to reach (the pocket drops out of the way).
          With reduced motion only visibility transitions: it must never flip instantly, or Tab from the card
          hides these buttons before focus can land on them. */}
      <div className="invisible absolute inset-x-12 bottom-[124px] z-20 flex translate-y-3 flex-col items-stretch gap-2 opacity-0 transition-all duration-300 peek:visible peek:translate-y-0 peek:opacity-100 motion-reduce:transition-[visibility]">
        {price && <BuyButton level={level} price={formatPrice(price.cents, price.currency)} floating />}
        {pack && nextName && (
          <PackButton level={level} nextName={nextName} price={formatPrice(pack.cents, pack.currency)} />
        )}
        <PreviewButton level={level} hasPreview={hasPreview} floating />
        {price && (
          <a
            href={`/gift?for=${level.slug}`}
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center justify-center gap-1 self-center rounded-full bg-white/90 px-3 py-0.5 text-[0.8rem] font-extrabold underline-offset-2 hover:underline"
          >
            <Gift className="size-3.5 text-coral" /> Give as a gift
          </a>
        )}
      </div>

      {/* The pocket: slides down on hover / tap to reveal the sheet. */}
      <div
        className={cn(
          "absolute inset-x-0 bottom-0 z-10 h-[64%] rounded-t-[1.75rem] border-t-[3px] border-ink p-5 text-ink transition-transform duration-500 ease-[cubic-bezier(.2,.9,.3,1.1)]",
          "peek:translate-y-[calc(100%-62px)] motion-reduce:transition-none",
          BG[level.color],
        )}
      >
        <div className="flex items-baseline justify-between gap-2">
          <h3 className="text-3xl font-bold leading-none">{level.name}</h3>
          <p className="shrink-0 text-sm font-extrabold opacity-80">Age {level.age}</p>
        </div>
        <div className="mt-2 flex items-center gap-2 transition-all duration-300 peek:invisible peek:opacity-0">
          <PreviewButton level={level} hasPreview={hasPreview} />
          {price && <BuyButton level={level} price={formatPrice(price.cents, price.currency)} />}
        </div>

        <div className="mt-3 flex items-end gap-3 transition-opacity duration-300 peek:opacity-0">
          <div className="flex shrink-0 flex-col items-center gap-1">
            <img src={level.mascot} alt="" className="mascot-bob size-16 rounded-full border-[3px] border-ink bg-white p-1.5" />
            <span
              title={Object.entries(level.pages)
                .map(([s, n]) => `${n} ${SUBJECT_LABEL[s as keyof typeof SUBJECT_LABEL].toLowerCase()}`)
                .join(" + ")}
              className="text-xs font-extrabold whitespace-nowrap"
            >
              {level.totalPages} pages
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <span className="rounded-full border-2 border-ink bg-ink px-2.5 py-0.5 text-xs font-extrabold text-white">
              {gradeLabel(level.grade)}
            </span>

            {level.subjects.map((s) => (
              <span
                key={s}
                title={`${level.pages[s]} pages of ${SUBJECT_LABEL[s].toLowerCase()}`}
                className="rounded-full border-2 border-ink bg-white px-2.5 py-0.5 text-xs font-extrabold"
              >
                {SUBJECT_LABEL[s]}
              </span>
            ))}
            {!ready && (
              <span className="rounded-full border-2 border-dashed border-ink bg-white/60 px-2.5 py-0.5 text-xs font-extrabold">
                Coming soon
              </span>
            )}
          </div>
        </div>
        <p className="mt-3 text-[0.95rem] font-semibold leading-snug transition-opacity duration-300 peek:opacity-0">
          {level.blurb}
        </p>
      </div>
    </article>
  );
}

/** Big "pill-pop" buttons (ink border + offset shadow, like the header's Shop levels) for the floating row. */
const FLOAT = "pill-pop justify-center rounded-full px-4 py-1 text-[0.95rem]";

function PreviewButton({ level, hasPreview, floating }: { level: Level; hasPreview: boolean; floating?: boolean }) {
  if (hasPreview) {
    return (
      <a
        href={`/api/previews/${level.slug}`}
        onClick={(e) => e.stopPropagation()}
        className={cn(
          "inline-flex shrink-0 items-center gap-1 font-extrabold",
          floating
            ? cn(FLOAT, "bg-white")
            : "rounded-full border-2 border-ink bg-white px-2.5 py-1.5 text-[0.8rem] transition-transform hover:-translate-y-0.5 active:translate-y-0",
        )}
      >
        <Download className="size-4" /> Free preview
      </a>
    );
  }
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center gap-1 rounded-full border-2 border-dashed border-ink/60 px-2.5 py-1.5 text-xs font-extrabold text-ink/70",
        floating ? "bg-white" : "bg-white/50",
      )}
    >
      <Sparkles className="size-3.5" /> Preview soon
    </span>
  );
}

function BuyButton({ level, price, floating }: { level: Level; price: string; floating?: boolean }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <>
      <button
        type="button"
        disabled={busy}
        onClick={async (e) => {
          e.stopPropagation();
          setBusy(true);
          setError(await startCheckout(level.slug));
          setBusy(false);
        }}
        aria-label={`Buy the whole ${level.name} level for ${price}`}
        className={cn(
          "inline-flex shrink-0 items-center gap-1 font-extrabold disabled:opacity-70",
          floating
            ? cn(FLOAT, "bg-sun text-ink")
            : "rounded-full border-2 border-ink bg-ink px-2.5 py-1.5 text-[0.8rem] text-white transition-transform hover:-translate-y-0.5 active:translate-y-0",
        )}
      >
        {busy ? <Loader2 className="size-4 animate-spin" /> : <ShoppingBag className="size-4" />} Buy {price}
      </button>
      {error && <ErrorToast message={error} onClose={() => setError(null)} />}
    </>
  );
}

/** A level plus the next one on the ladder (the "two" bundle). */
function PackButton({ level, nextName, price }: { level: Level; nextName: string; price: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <>
      <button
        type="button"
        disabled={busy}
        onClick={async (e) => {
          e.stopPropagation();
          setBusy(true);
          setError(await startCheckout(level.slug, "two"));
          setBusy(false);
        }}
        aria-label={`Buy ${level.name} and ${nextName} together for ${price}`}
        className={cn(FLOAT, "inline-flex items-center gap-1 whitespace-nowrap bg-white px-3 text-[0.8rem] disabled:opacity-70")}
      >
        {busy && <Loader2 className="size-4 animate-spin" />} + {nextName}: both {price}
      </button>
      {error && <ErrorToast message={error} onClose={() => setError(null)} />}
    </>
  );
}

function ErrorToast({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <div
      onClick={(e) => {
        e.stopPropagation();
        onClose();
      }}
      role="alert"
      className="absolute inset-x-3 -top-14 z-20 rounded-xl border-2 border-ink bg-white px-3 py-2 text-sm font-bold shadow"
    >
      {message}
    </div>
  );
}

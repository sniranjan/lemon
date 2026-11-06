import { useEffect, useState } from "react";
import { Download, Sparkles } from "lucide-react";
import { LEVELS, SUBJECT_LABEL, type Level } from "@/data/levels";
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

/** Which levels have a free preview PDF uploaded to R2 (asked once from the Worker). */
function usePreviews() {
  const [available, setAvailable] = useState<Set<string>>(new Set());
  useEffect(() => {
    fetch("/api/previews")
      .then((r) => (r.ok ? (r.json() as Promise<{ previews: string[] }>) : { previews: [] }))
      .then((d: { previews: string[] }) => setAvailable(new Set(d.previews)))
      .catch(() => {});
  }, []);
  return available;
}

export function Library() {
  const available = usePreviews();
  return (
    <section id="library" className="scroll-mt-24 px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <SectionHeading eyebrow="the library" title="Twelve levels, one big climb">
          Every level has reading and math, from age 3 to 12, and runs a little ahead of school.
          <span className="hidden sm:inline"> Hover a level to peek at a sheet.</span>
          <span className="sm:hidden"> Tap a level to peek at a sheet.</span>
        </SectionHeading>
        <div className="mt-12 grid gap-7 sm:grid-cols-2 lg:grid-cols-4">
          {LEVELS.map((level, i) => (
            <LevelCard key={level.slug} level={level} index={i} hasPreview={available.has(level.slug)} />
          ))}
        </div>
      </div>
    </section>
  );
}

function LevelCard({ level, index, hasPreview }: { level: Level; index: number; hasPreview: boolean }) {
  const [open, setOpen] = useState(false);
  const ready = level.status === "ready";
  return (
    <article
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
      className="card-rise sticker group relative h-[440px] cursor-pointer overflow-hidden bg-cream outline-none transition-transform duration-300 hover:-translate-y-1 focus-visible:ring-4 focus-visible:ring-sky motion-reduce:transition-none"
      style={{ animationDelay: `${index * 70}ms` }}
    >
      {/* The sheet, tucked into the pocket. */}
      <div
        className="absolute inset-x-5 top-5 h-[318px] origin-bottom -rotate-2 transition-transform duration-500 ease-[cubic-bezier(.2,.9,.3,1.2)] peek:rotate-0 peek:scale-[1.02] motion-reduce:transition-none"
      >
        <SheetPreview level={level} className="h-full" />
      </div>

      {/* The pocket: slides down on hover / tap to reveal the sheet. */}
      <div
        className={cn(
          "absolute inset-x-0 bottom-0 z-10 h-[64%] rounded-t-[1.75rem] border-t-[3px] border-ink p-5 text-ink transition-transform duration-500 ease-[cubic-bezier(.2,.9,.3,1.1)]",
          "peek:translate-y-[calc(100%-92px)] motion-reduce:transition-none",
          BG[level.color],
        )}
      >
        <h3 className="text-3xl font-bold leading-none">{level.name}</h3>
        <div className="mt-1.5 flex items-center justify-between gap-2">
          <p className="text-sm font-bold opacity-80">Ages {level.ages}</p>
          <PreviewButton level={level} hasPreview={hasPreview} />
        </div>

        <div className="mt-3 flex items-end gap-3 transition-opacity duration-300 peek:opacity-0">
          <img src={level.mascot} alt="" className="mascot-bob size-16 shrink-0 rounded-full border-[3px] border-ink bg-white p-1.5" />
          <div className="flex flex-wrap gap-1.5">
            {level.subjects.map((s) => (
              <span key={s} className="rounded-full border-2 border-ink bg-white px-2.5 py-0.5 text-xs font-extrabold">
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

function PreviewButton({ level, hasPreview }: { level: Level; hasPreview: boolean }) {
  if (hasPreview) {
    return (
      <a
        href={`/api/previews/${level.slug}`}
        onClick={(e) => e.stopPropagation()}
        className="inline-flex shrink-0 items-center gap-1.5 rounded-full border-2 border-ink bg-white px-3 py-1.5 text-sm font-extrabold transition-transform hover:-translate-y-0.5 active:translate-y-0"
      >
        <Download className="size-4" /> Free preview
      </a>
    );
  }
  return (
    <span className="inline-flex shrink-0 items-center gap-1 rounded-full border-2 border-dashed border-ink/60 bg-white/50 px-3 py-1.5 text-xs font-extrabold text-ink/70">
      <Sparkles className="size-3.5" /> Preview soon
    </span>
  );
}

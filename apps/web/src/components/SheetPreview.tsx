import type { Level, Preview } from "@/data/levels";
import { SUBJECT_LABEL } from "@/data/levels";
import { cn } from "@/lib/utils";

const NUMBER_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"];

function Pic({ name, className }: { name: string; className?: string }) {
  return <img src={`/pictures/${name}.svg`} alt="" className={cn("shrink-0", className)} draggable={false} />;
}

/** A miniature practice sheet, drawn in HTML so it stays sharp and light. */
export function SheetPreview({ level, className }: { level: Level; className?: string }) {
  return (
    <div
      className={cn(
        "flex flex-col rounded-lg border-2 border-ink/80 bg-white p-3 text-ink shadow-[0_2px_0_0_rgba(31,42,68,0.25)]",
        className,
      )}
    >
      <div className="flex items-baseline justify-between gap-2 border-b-2 pb-1" style={{ borderColor: `var(--${level.color})` }}>
        <span className="text-[9px] font-extrabold uppercase tracking-[0.14em] text-ink/60">
          {level.name} · {SUBJECT_LABEL[level.subjects[0]]}
        </span>
        <span className="text-[9px] text-ink/50">Name ______</span>
      </div>
      <div className="flex flex-1 flex-col justify-start gap-2 pt-3">
        <Body preview={level.preview} />
      </div>
    </div>
  );
}

function Body({ preview }: { preview: Preview }) {
  switch (preview.kind) {
    case "words":
      return (
        <>
          {preview.words.map((w) => (
            <div key={w.word} className="flex items-center gap-3 rounded-2xl border-2 border-ink px-3 py-1.5">
              <Pic name={w.picture} className="size-14" />
              <span className="font-display text-3xl font-bold">{w.word}</span>
            </div>
          ))}
          <div className="flex items-center gap-2 rounded-xl border border-dashed border-ink/40 px-2 py-1 text-[9px] text-ink/60">
            Say it again:
            <Pic name="cat" className="size-5" /> cat
            <Pic name="sun" className="size-5" /> sun
          </div>
        </>
      );
    case "path":
      return (
        <svg viewBox="0 0 240 150" className="w-full">
          <path
            d="M24 110 C 80 20, 150 140, 200 50"
            fill="none" stroke="#d9dde6" strokeWidth="30" strokeLinecap="round"
          />
          <path
            d="M24 110 C 80 20, 150 140, 200 50"
            fill="none" stroke="var(--ink)" strokeWidth="3" strokeDasharray="2 9" strokeLinecap="round"
            className="path-draw"
          />
          <circle cx="24" cy="110" r="8" fill="var(--ink)" />
          <image href={`/pictures/${preview.from}.svg`} x="2" y="122" width="26" height="26" />
          <circle cx="200" cy="50" r="24" fill="#fff" stroke="var(--ink)" strokeWidth="2" />
          <image href={`/pictures/${preview.to}.svg`} x="182" y="32" width="36" height="36" />
        </svg>
      );
    case "count":
      return (
        <div className="flex items-center gap-3 rounded-2xl border-2 border-ink p-3">
          <div className="grid flex-1 grid-cols-3 gap-1">
            {Array.from({ length: preview.n }, (_, i) => (
              <Pic key={i} name={preview.picture} className="size-11" />
            ))}
          </div>
          <div className="text-center">
            <div className="font-display text-6xl font-bold leading-none">{preview.n}</div>
            <div className="text-sm font-bold">{NUMBER_WORDS[preview.n]}</div>
          </div>
        </div>
      );
    case "phrase":
      return (
        <div className="flex flex-col items-center gap-2 rounded-2xl border-2 border-ink p-3">
          <Pic name={preview.picture} className="size-20" />
          <span className="font-display text-3xl font-bold">{preview.phrase}</span>
        </div>
      );
    case "trace":
      return (
        <div className="flex items-center gap-2 rounded-2xl border-2 border-ink p-2">
          <div className="flex flex-col items-center">
            <Pic name={preview.picture} className="size-14" />
            <span className="font-display text-lg font-bold">{preview.word}</span>
          </div>
          <svg viewBox="0 0 150 90" className="flex-1">
            {[0, 1, 2].map((i) => (
              <text
                key={i}
                x={10 + i * 48}
                y="72"
                fontSize="80"
                fontFamily="Fredoka, sans-serif"
                fontWeight="600"
                fill="none"
                stroke={i === 0 ? "var(--ink)" : "#9aa1b2"}
                strokeWidth="2.5"
                strokeDasharray={i === 0 ? undefined : "3 5"}
                strokeLinecap="round"
              >
                {preview.letter}
              </text>
            ))}
          </svg>
        </div>
      );
    case "write":
      return (
        <div className="flex flex-col gap-2">
          <div className="flex justify-between">
            {preview.numbers.map((n) => (
              <span key={n} className="font-display text-4xl font-semibold text-transparent [-webkit-text-stroke:1.5px_#8a92a6]">
                {n}
              </span>
            ))}
          </div>
          <div className="flex justify-between">
            {preview.numbers.map((n) => (
              <span key={n} className="size-10 rounded-full border-2 border-ink" />
            ))}
          </div>
          <div className="flex justify-between">
            {preview.numbers.map((n) => (
              <span key={n} className="size-10 rounded-full border-2 border-ink" />
            ))}
          </div>
        </div>
      );
    case "add":
      return (
        <div className="flex flex-col gap-1.5">
          {preview.facts.map(([a, b], i) => (
            <div key={i} className="flex items-center gap-3 font-display text-2xl font-semibold">
              {i === 0 && (
                <span className="flex items-center gap-1 text-base text-ink/60">
                  {a} → <span className="inline-block size-6 rounded border-2 border-ink/60" />
                </span>
              )}
              <span className={i === 0 ? "" : "pl-[4.25rem]"}>
                {a} + {b} =
              </span>
              <span className="inline-block h-7 w-9 rounded-md border-2 border-ink" />
            </div>
          ))}
        </div>
      );
    case "read":
      return (
        <div className="flex flex-col gap-2">
          <Pic name={preview.picture} className="mx-auto size-16" />
          {preview.lines.map((l) => (
            <p key={l} className="font-display text-xl font-semibold leading-tight">
              {l}
            </p>
          ))}
        </div>
      );
  }
}

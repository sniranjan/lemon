import { cn } from "@/lib/utils";

/** The mark: a smiling sheet of paper with a folded corner. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" aria-hidden="true" className={cn("shrink-0", className)}>
      <path
        d="M12 6 H42 L54 18 V56 a2 2 0 0 1-2 2 H12 a2 2 0 0 1-2-2 V8 a2 2 0 0 1 2-2 Z"
        fill="var(--sun)" stroke="var(--ink)" strokeWidth="4" strokeLinejoin="round"
      />
      <path d="M42 6 V18 H54" fill="#fff" stroke="var(--ink)" strokeWidth="4" strokeLinejoin="round" />
      <circle cx="24" cy="32" r="3.2" fill="var(--ink)" />
      <circle cx="40" cy="32" r="3.2" fill="var(--ink)" />
      <path d="M23 41 Q32 49 41 41" fill="none" stroke="var(--ink)" strokeWidth="4" strokeLinecap="round" />
    </svg>
  );
}

/** Wordmark: "paper" chunky and round, "lessons" in crayon handwriting. Reads as one word: paperlessons. */
export function Logo({ className, size = "md" }: { className?: string; size?: "md" | "lg" }) {
  const big = size === "lg";
  return (
    <a href="/" aria-label="paperlessons home" className={cn("group inline-flex items-center gap-2", className)}>
      <LogoMark className={cn(big ? "size-14" : "size-7 min-[400px]:size-8 sm:size-10", "transition-transform group-hover:-rotate-6")} />
      <span className={cn("leading-none whitespace-nowrap", !big && "max-[349px]:hidden", big ? "text-5xl" : "text-[1.25rem] min-[400px]:text-[1.55rem] sm:text-[1.9rem]")}>
        <span className="font-display font-bold tracking-tight text-ink">paper</span>
        <span className="font-hand text-coral inline-block -rotate-3 translate-y-0.5 text-[1.12em]">lessons</span>
      </span>
    </a>
  );
}

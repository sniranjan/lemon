import type { ReactNode } from "react";

/** Small hand-written eyebrow over a big rounded heading, used by every section. */
export function SectionHeading({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return (
    <div className="mx-auto max-w-2xl text-center">
      <p className="font-hand text-2xl text-coral">{eyebrow}</p>
      <h2 className="mt-1 text-balance text-4xl font-bold sm:text-5xl">{title}</h2>
      {children && <p className="mt-4 text-lg text-muted-foreground">{children}</p>}
    </div>
  );
}

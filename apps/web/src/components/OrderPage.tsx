import { useEffect, useState } from "react";
import { Download, FileText, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { LEVELS } from "@/data/levels";

type Order = {
  ok: true;
  level: { slug: string; name: string; title: string; age: number };
  email: string | null;
  purchasedAt: string;
  expiresAt: string | null;
  files: { name: string; size: number; url: string }[];
};

type State =
  | { kind: "loading" }
  | { kind: "pending" }
  | { kind: "expired" }
  | { kind: "error"; message: string }
  | { kind: "ready"; order: Order; token: string };

/** "2026-11-13 14:41:14" (UTC, from D1) → "November 13, 2026". */
function longDate(sqlUtc: string): string {
  return new Intl.DateTimeFormat("en-US", { dateStyle: "long", timeZone: "UTC" }).format(new Date(`${sqlUtc.replace(" ", "T")}Z`));
}

/** "chicks-reading-level.pdf" → "Reading: the whole level". */
function fileLabel(name: string): string {
  const base = name.replace(/\.pdf$/, "");
  const subject = /reading/.test(base) ? "Reading" : /math/.test(base) ? "Math" : /pencil/.test(base) ? "Pencil skills" : null;
  const what = /answers/.test(base) ? "answer key" : /level/.test(base) ? "the whole level" : base;
  return subject ? `${subject}: ${what}` : what;
}

function mb(bytes: number): string {
  return `${(bytes / 1_048_576).toFixed(bytes < 10_485_760 ? 1 : 0)} MB`;
}

/**
 * /thanks?session_id=… (Stripe's return address) and /orders/<token> (the link to keep).
 * The thanks page swaps itself for the order address once the payment is confirmed.
 */
export function OrderPage() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let stop = false;
    async function load() {
      let token = location.pathname.match(/^\/orders\/([A-Za-z0-9_-]+)$/)?.[1] ?? null;
      const sid = new URLSearchParams(location.search).get("session_id");
      // Coming back from Stripe: the webhook may land a moment later, so ask a few times.
      for (let i = 0; !token && sid && i < 8 && !stop; i++) {
        const r = await fetch(`/api/orders/session/${encodeURIComponent(sid)}`);
        const d = (await r.json().catch(() => ({}))) as { ok?: boolean; token?: string; pending?: boolean; error?: string };
        if (d.ok && d.token) {
          token = d.token;
          history.replaceState(null, "", `/orders/${token}`);
        } else if (d.pending) {
          setState({ kind: "pending" });
          await new Promise((res) => setTimeout(res, 1500));
        } else {
          break;
        }
      }
      if (stop) return;
      if (!token) {
        setState({ kind: "error", message: "We couldn't find that order. If you were charged, reply to your payment receipt and we'll sort it out." });
        return;
      }
      const r = await fetch(`/api/orders/${token}`);
      const d = (await r.json().catch(() => ({}))) as Order | { ok: false; expired?: boolean; error?: string };
      if (!stop) {
        setState(
          d.ok
            ? { kind: "ready", order: d, token }
            : d.expired
              ? { kind: "expired" }
              : { kind: "error", message: d.error ?? "We couldn't find that order." },
        );
      }
    }
    load();
    return () => {
      stop = true;
    };
  }, []);

  return (
    <section className="px-4 py-16 sm:px-6 sm:py-24">
      <div className="sticker mx-auto max-w-2xl bg-white p-6 sm:p-10">
        {state.kind === "loading" || state.kind === "pending" ? (
          <div className="flex items-center gap-3 text-lg font-bold">
            <Loader2 className="size-6 animate-spin text-coral" />
            {state.kind === "pending" ? "Confirming your payment…" : "Finding your order…"}
          </div>
        ) : state.kind === "expired" ? (
          <>
            <p className="font-hand text-2xl text-coral">sorry!</p>
            <h1 className="text-3xl font-bold">This link has expired</h1>
            <p className="mt-3 text-lg text-ink/80">
              Download links work for 7 days after purchase. If you need your files again, email{" "}
              <a className="font-bold text-coral underline underline-offset-2" href="mailto:hello@paperlessons.com">
                hello@paperlessons.com
              </a>{" "}
              from the address you bought with.
            </p>
            <Button asChild variant="coral" size="pill" className="mt-6">
              <a href="/">Back to paperlessons</a>
            </Button>
          </>
        ) : state.kind === "error" ? (
          <>
            <h1 className="text-3xl font-bold">Hmm, something's missing</h1>
            <p className="mt-3 text-lg text-ink/80">{state.message}</p>
            <Button asChild variant="coral" size="pill" className="mt-6">
              <a href="/">Back to paperlessons</a>
            </Button>
          </>
        ) : (
          <Ready order={state.order} />
        )}
      </div>
    </section>
  );
}

function Ready({ order }: { order: Order }) {
  const look = LEVELS.find((l) => l.slug === order.level.slug);
  return (
    <>
      <div className="flex items-center gap-4">
        {look && <img src={look.mascot} alt="" className="size-16 rounded-full border-[3px] border-ink bg-cream p-1.5" />}
        <div>
          <p className="font-hand text-2xl text-coral">thank you!</p>
          <h1 className="text-3xl font-bold leading-tight sm:text-4xl">{order.level.name} is all yours</h1>
        </div>
      </div>
      <p className="mt-4 text-lg text-ink/80">
        {order.level.title}. Print the pages a few at a time, or all at once, and keep the answer keys for yourself.
      </p>

      {order.files.length ? (
        <ul className="mt-6 flex flex-col gap-3">
          {order.files.map((f) => (
            <li key={f.name}>
              <a
                href={f.url}
                className="flex items-center gap-3 rounded-xl border-[3px] border-ink bg-cream px-4 py-3 font-bold transition-transform hover:-translate-y-0.5"
              >
                <FileText className="size-6 shrink-0 text-coral" />
                <span className="flex-1">{fileLabel(f.name)}</span>
                <span className="text-sm text-ink/60">{mb(f.size)}</span>
                <Download className="size-5 shrink-0" />
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-6 rounded-xl border-2 border-dashed border-ink/50 p-4 font-bold">
          Your files are being prepared. Check back on this page shortly.
        </p>
      )}

      <div className="mt-8 rounded-xl bg-sun/30 p-4 text-ink/80">
        <p className="font-bold text-ink">
          {order.expiresAt ? `This link works until ${longDate(order.expiresAt)}` : "Download your files now"}
        </p>
        <p className="mt-1">
          Download and save your files now: after 7 days this link expires.
          {order.email ? ` We've also emailed it to ${order.email}.` : ""} Please don't share it.
        </p>
      </div>
    </>
  );
}

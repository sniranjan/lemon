import { useState, type FormEvent } from "react";
import { Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const AGES = ["2", "3", "4", "5", "6", "7+"];

export function Waitlist() {
  const [email, setEmail] = useState("");
  const [age, setAge] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    setState("sending");
    try {
      const r = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, childAge: age || undefined }),
      });
      const d = (await r.json()) as { ok: boolean; error?: string };
      if (!d.ok) throw new Error(d.error || "Something went wrong.");
      setState("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setState("error");
    }
  }

  if (state === "done") {
    return (
      <div className="flex items-center justify-center gap-3 rounded-xl border-[3px] border-ink bg-white px-5 py-4 text-lg font-bold text-ink pop">
        <span className="grid size-8 place-items-center rounded-full bg-leaf"><Check className="size-5" /></span>
        You're on the list! We'll email you when downloads open.
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-3">
      <div className="flex flex-col gap-3 sm:flex-row">
        <label className="sr-only" htmlFor="wl-email">Email</label>
        <Input
          id="wl-email"
          type="email"
          required
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="h-13 flex-1 rounded-full border-[3px] border-ink bg-white px-5 text-lg text-ink shadow-none"
        />
        <label className="sr-only" htmlFor="wl-age">Child's age</label>
        <select
          id="wl-age"
          value={age}
          onChange={(e) => setAge(e.target.value)}
          className="h-13 rounded-full border-[3px] border-ink bg-white px-4 text-lg font-semibold text-ink outline-none focus-visible:ring-4 focus-visible:ring-sky"
        >
          <option value="">Child's age</option>
          {AGES.map((a) => (
            <option key={a} value={a}>{a} years</option>
          ))}
        </select>
        <Button
          type="submit"
          disabled={state === "sending"}
          className="h-13 rounded-full border-[3px] border-ink px-7 text-lg font-extrabold pop transition-transform hover:-translate-y-0.5 active:translate-y-0.5 active:shadow-none"
        >
          {state === "sending" ? <Loader2 className="size-5 animate-spin" /> : "Tell me first"}
        </Button>
      </div>
      {state === "error" && <p className="w-fit rounded-full bg-white px-3 py-1 text-sm font-bold text-destructive" role="alert">{error}</p>}
      <p className="text-sm font-semibold opacity-85">One email when downloads open. No spam, ever.</p>
    </form>
  );
}

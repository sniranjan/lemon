import { ArrowDown, BookOpen, Calculator, Pencil, Printer, Sprout, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/Logo";
import { SectionHeading } from "@/components/SectionHeading";
import { LegalLinks, LegalPage, isLegalPath } from "@/components/LegalPage";
import { CookieBanner } from "@/components/CookieBanner";
import { Library } from "@/components/Library";
import { consentRequired, openCookieSettings } from "@/lib/consent";
import { OrderPage } from "@/components/OrderPage";
import { SheetPreview } from "@/components/SheetPreview";
import { Waitlist } from "@/components/Waitlist";
import { LEVELS } from "@/data/levels";

/** Order pages: Stripe returns to /thanks, and each order lives at /orders/<token>. */
const isOrderPage = () => location.pathname === "/thanks" || location.pathname.startsWith("/orders/");

const bySlug = (s: string) => LEVELS.find((l) => l.slug === s)!;

export default function App() {
  return (
    <div className="min-h-screen overflow-x-clip">
      <Nav />
      {isOrderPage() ? (
        <main>
          <OrderPage />
        </main>
      ) : isLegalPath(location.pathname) ? (
        <main>
          <LegalPage path={location.pathname} />
        </main>
      ) : (
        <main>
          <Hero />
          <HowItWorks />
          <Library />
          <Subjects />
          <EarlyAccess />
          <Faq />
        </main>
      )}
      <Footer />
      <CookieBanner />
    </div>
  );
}

function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b-[3px] border-ink bg-cream/90 backdrop-blur">
      <div className="mx-auto flex h-18 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Logo />
        <nav className="flex items-center gap-1 text-[0.95rem] font-extrabold sm:gap-2">
          <a href="/#how" className="hidden rounded-full px-3 py-2 hover:bg-white sm:inline">
            How it works
          </a>
          <a href="/#library" className="hidden rounded-full px-3 py-2 hover:bg-white sm:inline">
            Library
          </a>
          <Button asChild variant="sun" size="pill-sm">
            <a href="/#early">Early access</a>
          </Button>
        </nav>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative px-4 pb-16 pt-14 sm:px-6 sm:pt-20">
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-10 top-24 size-40 rounded-full bg-sun/40" />
        <div className="absolute -right-16 top-10 size-56 rounded-full bg-sky/20" />
      </div>
      <div className="relative mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-[1.1fr_1fr]">
        <div>
          <p className="inline-flex items-center gap-2 rounded-full border-2 border-ink bg-white px-3 py-1 text-sm font-extrabold">
            <Sun className="size-4 text-coral" /> For ages 3 to 12
          </p>
          <h1 className="mt-5 text-5xl font-bold leading-[1.05] tracking-tight sm:text-6xl lg:text-[4.1rem]">
            Little <span className="inline-block -rotate-2 font-hand text-[1.08em] text-coral">lessons</span>,
            <br />
            one page at a time.
          </h1>
          <p className="mt-6 max-w-xl text-xl leading-relaxed text-ink/80">
            Printable reading and math sheets that run about two grades ahead of school, from first words and counting
            to fractions and algebra. A few pages a day, one small step at a time.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild variant="coral" size="pill">
              <a href="#library">
                Peek at the library <ArrowDown className="size-5" />
              </a>
            </Button>
            <Button asChild variant="paper" size="pill">
              <a href="#early">Get early access</a>
            </Button>
          </div>
        </div>

        {/* A small fan of sheets. */}
        <div className="relative mx-auto h-[400px] w-full max-w-[440px]" aria-hidden="true">
          <SheetPreview
            level={bySlug("owls")}
            className="float absolute left-0 top-10 h-[300px] w-[230px] [--r:-8deg]"
          />
          <SheetPreview
            level={bySlug("ducklings")}
            className="float absolute right-0 top-0 h-[300px] w-[230px] [--r:7deg] [animation-delay:-2s]"
          />
          <SheetPreview
            level={bySlug("chicks")}
            className="float absolute left-1/2 top-20 h-[310px] w-[240px] -translate-x-1/2 [--r:-1deg] [animation-delay:-4s]"
          />
        </div>
      </div>
    </section>
  );
}

const STEPS = [
  {
    icon: Sprout,
    color: "bg-leaf",
    title: "Pick a level",
    text: "Start with the animal that fits. Little ones begin with Chicks; older kids jump in higher up.",
  },
  {
    icon: Printer,
    color: "bg-sky",
    title: "Get the whole level",
    text: "One PDF with every page in order. Print it all at once, or a week's worth at a time. Black and white is fine.",
  },
  {
    icon: Sun,
    color: "bg-sun",
    title: "A little every day",
    text: "A few pages, about ten minutes. When three pages in a row feel easy, they're ready for the next step.",
  },
];

function HowItWorks() {
  return (
    <section id="how" className="scroll-mt-24 border-y-[3px] border-ink bg-white px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <SectionHeading eyebrow="how it works" title="Small steps, every day" />
        <ol className="mt-12 grid gap-6 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <li key={s.title} className="sticker relative bg-cream p-6">
              <span className="absolute right-5 top-3 font-hand text-5xl text-ink/15">{i + 1}</span>
              <span className={`grid size-14 place-items-center rounded-2xl border-[3px] border-ink ${s.color}`}>
                <s.icon className="size-7" />
              </span>
              <h3 className="mt-4 text-2xl font-bold">{s.title}</h3>
              <p className="mt-2 text-lg leading-relaxed text-ink/80">{s.text}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

const SUBJECTS = [
  {
    icon: BookOpen,
    color: "bg-teal",
    title: "Reading",
    text: "From first picture words to reading whole stories and explaining them, with every new word coming back until it sticks.",
  },
  {
    icon: Calculator,
    color: "bg-coral",
    title: "Math",
    text: "From counting to ten all the way to times tables, fractions, percents and linear equations, one small step at a time.",
  },
  {
    icon: Pencil,
    color: "bg-grape",
    title: "Pencil warm-ups",
    text: "In the first two levels: coloring and drawing lines from a dot to a picture, so little hands are ready to write.",
  },
];

function Subjects() {
  return (
    <section className="border-y-[3px] border-ink bg-sun/30 px-4 py-20 sm:px-6">
      <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-3">
        {SUBJECTS.map((s) => (
          <div key={s.title} className="sticker bg-white p-6">
            <span
              className={`grid size-12 place-items-center rounded-full border-[3px] border-ink text-white ${s.color}`}
            >
              <s.icon className="size-6" />
            </span>
            <h3 className="mt-4 text-2xl font-bold">{s.title}</h3>
            <p className="mt-2 text-lg leading-relaxed text-ink/80">{s.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function EarlyAccess() {
  return (
    <section id="early" className="scroll-mt-24 px-4 py-20 sm:px-6">
      <div className="sticker relative mx-auto max-w-3xl bg-teal p-8 text-white sm:p-12">
        <img src="/pictures/star.svg" alt="" className="mascot-bob absolute -right-5 -top-7 size-16" />
        <p className="font-hand text-2xl text-sun">coming soon</p>
        <h2 className="mt-1 text-4xl font-bold sm:text-5xl">Download, print, play.</h2>
        <p className="mt-4 max-w-xl text-lg text-white/90">
          Whole levels as printable PDFs are on their way, and printed sets shipped to your door after that. Leave your
          email and we'll tell you the moment they're ready.
        </p>
        <div className="mt-8">
          <Waitlist />
        </div>
      </div>
    </section>
  );
}

const FAQ = [
  {
    q: "What age is this for?",
    a: "Ages 3 to 12. The work runs about two grades ahead of school, so a first grader works on third-grade reading and math, one small step at a time. Start where your child feels confident, even if that's a little below their age. Easy is good: it builds the habit.",
  },
  {
    q: "Do I need a color printer?",
    a: "No. Every sheet is designed to read clearly in black and white. The few color-word sheets are marked so you can print just those in color.",
  },
  {
    q: "How long does a day take?",
    a: "About ten minutes for little ones, 15 to 20 for older kids. Short and happy beats long and tired.",
  },
  {
    q: "Can I get a refund?",
    a: "No. Levels are instant digital downloads, so all sales are final. That's why every level has a free preview: try it with your child first. If a file doesn't work, email hello@paperlessons.com and we'll fix it.",
  },
  {
    q: "What if a level feels too hard?",
    a: "Go back a few pages and repeat them. Doing the same step again until it feels easy is how the next step becomes easy too.",
  },
];

function Faq() {
  return (
    <section className="px-4 pb-24 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <SectionHeading eyebrow="good questions" title="Questions grown-ups ask" />
        <div className="mt-10 flex flex-col gap-4">
          {FAQ.map((f) => (
            <details key={f.q} className="group rounded-xl border-[3px] border-ink bg-white p-5 open:pop">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-xl font-bold">
                {f.q}
                <span className="grid size-8 shrink-0 place-items-center rounded-full border-2 border-ink bg-sun transition-transform group-open:rotate-45">
                  +
                </span>
              </summary>
              <p className="mt-3 text-lg leading-relaxed text-ink/80">{f.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t-[3px] border-ink bg-white px-4 py-10 sm:px-6">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
        <Logo />
        <div className="flex flex-col items-center gap-1">
          <LegalLinks />
          {consentRequired() && (
            <button type="button" onClick={openCookieSettings} className="text-sm font-bold text-ink/70 hover:text-coral">
              Cookie settings
            </button>
          )}
        </div>
        <p className="text-sm font-semibold text-ink/60">
          © {new Date().getFullYear()} Madras Labs LLC · Made with care for little learners
        </p>
      </div>
    </footer>
  );
}

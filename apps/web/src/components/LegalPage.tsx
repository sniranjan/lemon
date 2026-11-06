import type { ReactNode } from "react";

// Privacy policy, terms of sale and refund policy: /privacy, /terms, /refunds.
// Plain-language, written for parents. Keep them in step with what the site actually does
// (worker/shop.ts, src/lib/replay.ts, the Google tag in index.html).

export const CONTACT = "hello@paperlessons.com";
const UPDATED = "November 6, 2026";

export const LEGAL_PATHS = ["/privacy", "/terms", "/refunds"] as const;
export type LegalPath = (typeof LEGAL_PATHS)[number];

export const isLegalPath = (p: string): p is LegalPath => (LEGAL_PATHS as readonly string[]).includes(p);

function Mail() {
  return (
    <a className="font-bold text-coral underline underline-offset-2" href={`mailto:${CONTACT}`}>
      {CONTACT}
    </a>
  );
}

function H({ children }: { children: ReactNode }) {
  return <h2 className="mt-10 text-2xl font-bold">{children}</h2>;
}

function Refunds() {
  return (
    <>
      <div className="mt-6 rounded-2xl border-[3px] border-ink bg-coral p-6 text-white">
        <p className="text-3xl font-bold leading-tight sm:text-4xl">All sales are final. No refunds.</p>
        <p className="mt-2 text-lg font-semibold text-white/95">
          Our levels are digital downloads you get instantly, so we can't take them back. Once you buy a level,
          we don't give refunds, exchanges or credit, for any reason.
        </p>
      </div>

      <H>Try before you buy</H>
      <p>
        Every level has a free preview PDF with real sample pages from that level. Please download it, print it and
        try it with your child before you buy, so you know the level is the right fit.
      </p>

      <H>Picking the right level</H>
      <p>
        Levels run about two grades ahead of school. If you're not sure where to start, start lower: easy pages
        build the habit. Buying a level that turns out to be too easy or too hard isn't a reason for a refund, so
        use the free previews to choose.
      </p>

      <H>If something is actually broken</H>
      <p>
        If a file won't download, won't open, or is missing pages, email <Mail /> within the 7 days your download
        link works and we'll fix it or send you a working file. That's a fix, not a refund. An expired link isn't a
        reason for a refund either, so please save your files when you buy. If you were charged twice for the same
        level by mistake, tell us and we'll refund the duplicate charge.
      </p>

      <H>Chargebacks</H>
      <p>
        Please talk to us before disputing a charge with your bank. If a charge is disputed, we may turn off the
        download link for that order while the dispute is open.
      </p>

      <H>Your legal rights</H>
      <p>
        This policy doesn't take away any right to a refund that the law where you live gives you and that can't be
        waived. By completing a purchase you ask us to give you the download straight away and agree that, once it's
        available, you lose any right to cancel that applies to digital content.
      </p>
    </>
  );
}

function Terms() {
  return (
    <>
      <H>Who we are</H>
      <p>
        paperlessons.com is a product of Madras Labs LLC ("we", "us"). These terms apply when you use the site or buy
        a level.
        By buying, you agree to them. Questions: <Mail />.
      </p>

      <H>What you buy</H>
      <p>
        A level is a set of printable PDF files (the pages, plus answer keys for grown-ups). After payment you get a
        private download link, on the page you return to and by email. <strong>The link works for 7 days after
        purchase and then expires</strong>, so download and save your files within that time. The link is for you
        alone: don't share it.
      </p>

      <H>Prices and payment</H>
      <p>
        Prices are shown in US dollars on the site and on the checkout page. Payment is handled by Stripe, which
        may act as the reseller (merchant of record) for your order and calculates any sales tax; its checkout terms
        apply to the payment itself. We never see or store your card number.
      </p>

      <H>Refunds</H>
      <p>
        <strong>All sales are final. No refunds.</strong> See the{" "}
        <a className="font-bold text-coral underline underline-offset-2" href="/refunds">
          refund policy
        </a>{" "}
        for the details, including what we do if a file doesn't work and the one exception (a duplicate charge by
        mistake).
      </p>

      <H>How you may use the pages</H>
      <ul className="list-disc space-y-2 pl-6">
        <li>
          <strong>Yes:</strong> print as many copies as you like for the children in your own home, as often as you
          like.
        </li>
        <li>
          <strong>No:</strong> sharing, reselling, uploading or giving the files (or printed copies) to other people,
          or using them in a classroom, tutoring business, school or co-op without a separate license from us.
        </li>
        <li>
          All pages, pictures, words and designs are ours and protected by copyright. Buying a level gives you a
          personal license to use it as above; it doesn't transfer ownership.
        </li>
      </ul>

      <H>Free previews</H>
      <p>Free preview PDFs are for trying the pages at home, under the same rules.</p>

      <H>Our promise, and its limits</H>
      <p>
        We work hard to make every page correct, age-appropriate and printable. The pages are practice material,
        not a guarantee of any school result. The site and files are provided "as is". To the fullest extent the law
        allows, we aren't liable for indirect or consequential losses, and our total liability for any purchase is
        limited to what you paid for it.
      </p>

      <H>Children</H>
      <p>
        The site and purchases are for parents and other adults. Children use the printed pages with a grown-up;
        they shouldn't use the site or buy anything themselves.
      </p>

      <H>Changes</H>
      <p>
        We may update these terms. The version on this page when you buy is the one that applies to that purchase.
      </p>
    </>
  );
}

function Privacy() {
  return (
    <>
      <p className="mt-6">
        paperlessons.com is a product of Madras Labs LLC ("we", "us"). This page explains what we collect on the site,
        why, and who else handles it. Questions or requests:{" "}
        <Mail />.
      </p>

      <H>What we collect</H>
      <ul className="list-disc space-y-2 pl-6">
        <li>
          <strong>Orders:</strong> your email address, the level you bought, the amount, and how many times your files
          were downloaded. We use your email to send you your download link (one email per order). Card details go
          straight to Stripe; we never see them.
        </li>
        <li>
          <strong>Free previews:</strong> which preview was downloaded and the country it was downloaded from (no
          name or email).
        </li>
        <li>
          <strong>Session recordings:</strong> we record how visitors use the site (pages viewed, including the
          address of your private order page, clicks, scrolling, and anything typed on the site) using OpenReplay, so
          we can see what's confusing and fix it. Recordings are not masked. Payment details are entered on Stripe's
          checkout page, which we don't record.
        </li>
        <li>
          <strong>Analytics:</strong> we use Google Tag Manager and Google Analytics, which set cookies and collect
          things like the pages you visit, your device and browser, and roughly where you are.
        </li>
        <li>
          <strong>Server logs:</strong> our host, Cloudflare, processes your IP address and basic request details to
          deliver and protect the site.
        </li>
      </ul>

      <H>What we don't do</H>
      <ul className="list-disc space-y-2 pl-6">
        <li>We don't sell your personal information or share it for advertising.</li>
        <li>
          We don't knowingly collect information from children. The site is for parents; if you think a child has
          given us their details, email us and we'll delete them.
        </li>
      </ul>

      <H>Who handles your data for us</H>
      <ul className="list-disc space-y-2 pl-6">
        <li>
          <strong>Cloudflare</strong>: hosting, our database and file storage.
        </li>
        <li>
          <strong>Stripe</strong>: payments and receipts (
          <a className="underline" href="https://stripe.com/privacy" rel="noreferrer" target="_blank">
            Stripe's privacy policy
          </a>
          ).
        </li>
        <li>
          <strong>Google</strong>: Tag Manager and Analytics (
          <a className="underline" href="https://policies.google.com/privacy" rel="noreferrer" target="_blank">
            Google's privacy policy
          </a>
          ).
        </li>
        <li>
          <strong>OpenReplay</strong>: session recordings, stored on a server we run.
        </li>
      </ul>

      <H>How long we keep it</H>
      <p>
        Orders are kept as long as you might need to download your files and as long as tax and accounting rules
        require. Session recordings and analytics are
        kept only as long as they're useful for improving the site.
      </p>

      <H>Your choices</H>
      <ul className="list-disc space-y-2 pl-6">
        <li>
          If you're in the EU/EEA, the UK or Switzerland, Google Analytics and session recording only start after you
          click "Accept all" on our cookie banner. "Reject all" keeps them off, and "Cookie settings" at the bottom of
          every page lets you change your choice.
        </li>
        <li>Email us to see, correct or delete the information we hold about you.</li>
        <li>You can block or clear cookies in your browser, and use Google's analytics opt-out add-on.</li>
        <li>Depending on where you live, you may have more rights under laws such as the GDPR or CCPA; email us to use them.</li>
      </ul>

      <H>Changes</H>
      <p>If we change how we use your information, we'll update this page and the date at the top.</p>
    </>
  );
}

const PAGES: Record<LegalPath, { title: string; eyebrow: string; body: () => ReactNode }> = {
  "/refunds": { title: "Refund policy", eyebrow: "the short version: no refunds", body: Refunds },
  "/terms": { title: "Terms of sale", eyebrow: "the fine print", body: Terms },
  "/privacy": { title: "Privacy policy", eyebrow: "your information", body: Privacy },
};

export function LegalPage({ path }: { path: LegalPath }) {
  const page = PAGES[path];
  return (
    <section className="px-4 py-16 sm:px-6 sm:py-20">
      <article className="mx-auto max-w-3xl text-lg leading-relaxed text-ink/85 [&_p]:mt-3 [&_ul]:mt-3">
        <p className="font-hand text-2xl text-coral">{page.eyebrow}</p>
        <h1 className="mt-1 text-4xl font-bold text-ink sm:text-5xl">{page.title}</h1>
        <p className="text-base text-ink/60">Last updated {UPDATED}</p>
        {page.body()}
        <nav className="mt-14 flex flex-wrap gap-3 border-t-2 border-ink/15 pt-6 text-base font-bold">
          {LEGAL_PATHS.filter((p) => p !== path).map((p) => (
            <a key={p} href={p} className="rounded-full border-2 border-ink bg-white px-4 py-1.5 hover:bg-sun">
              {PAGES[p].title}
            </a>
          ))}
        </nav>
      </article>
    </section>
  );
}

/** Small links for the footer. */
export function LegalLinks() {
  return (
    <nav className="flex flex-wrap justify-center gap-x-4 gap-y-1 text-sm font-bold text-ink/70">
      {LEGAL_PATHS.map((p) => (
        <a key={p} href={p} className="hover:text-coral">
          {PAGES[p].title}
        </a>
      ))}
    </nav>
  );
}

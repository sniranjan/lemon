// Order and gift emails, sent through Cloudflare's send_email binding from hello@paperlessons.com
// (Fastmail receives replies; Cloudflare signs outgoing mail for paperlessons.com).
// Senders return true once the message was handed to Cloudflare, false if there's no mailer or it failed.

export const FROM = { name: "paperlessons", email: "hello@paperlessons.com" };
/** Gift emails come from "Paper Lessons". The buyer's name only ever appears in the message, never in From. */
export const GIFT_FROM = { name: "Paper Lessons", email: "hello@paperlessons.com" };

/** "2026-11-13 14:41:14" (D1, UTC) or "2026-11-13" → "November 13, 2026". */
export function longDate(sqlUtc: string): string {
  const iso = sqlUtc.length === 10 ? `${sqlUtc}T12:00:00` : sqlUtc.replace(" ", "T");
  return new Intl.DateTimeFormat("en-US", { dateStyle: "long", timeZone: "UTC" }).format(new Date(`${iso}Z`));
}

export const esc = (s: string) => s.replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[ch]!);

const shell = (body: string, sign = "paperlessons") => `<!doctype html><html><body style="margin:0;background:#fff8ec;font-family:Nunito,Arial,sans-serif;color:#1f2a44">
<div style="max-width:520px;margin:0 auto;padding:32px 20px">
  <img src="https://paperlessons.com/brand/logo-email.png" width="200" alt="paperlessons" style="display:block;width:200px;height:auto;border:0">
${body}
  <p style="font-size:14px;color:#5b6478;line-height:1.5;margin:0">Questions? Just reply to this email.<br>${sign} · hello@paperlessons.com</p>
</div></body></html>`;

const button = (href: string, label: string) =>
  `<p style="margin:0 0 24px"><a href="${esc(href)}" style="display:inline-block;background:#1f2a44;color:#fff;text-decoration:none;font-weight:800;font-size:17px;padding:12px 22px;border-radius:999px">${esc(label)}</a></p>`;

/** Attachments go through the binding's message builder (Cloudflare writes the multipart/mixed MIME). */
async function send(
  mailer: SendEmail,
  from: typeof FROM,
  to: string,
  subject: string,
  text: string,
  html: string,
  what: string,
  attachments?: EmailAttachment[],
) {
  try {
    await mailer.send({ from, to, replyTo: from, subject, text, html, ...(attachments ? { attachments } : {}) });
    return true;
  } catch (e) {
    console.error(`${what} email failed`, e);
    return false;
  }
}

/** The download link for an order (bought, or opened with a gift: `gift` changes the thank-you line). */
export async function sendOrderEmail(
  mailer: SendEmail | undefined,
  o: { to: string; levelName: string; levelTitle: string; url: string; expiresAt: string; gift?: boolean },
): Promise<boolean> {
  if (!mailer) return false;
  const until = longDate(o.expiresAt);
  const subject = `Your ${o.levelName} pages are ready to download`;
  const opener = o.gift ? "Here are your gift pages:" : "Thank you for buying";
  const text = [
    `${opener} ${o.levelName} (${o.levelTitle}).`,
    "",
    `Download your PDFs here: ${o.url}`,
    "",
    `This link works for 7 days, until ${until}. After that it expires, so download and save your files now.`,
    "Please don't share the link or the files: they're for the children in your home.",
    "",
    "Print a few pages at a time, or all at once. Have fun!",
    "paperlessons · hello@paperlessons.com",
  ].join("\n");
  const html = shell(`  <h1 style="font-size:26px;margin:24px 0 8px">Your ${esc(o.levelName)} pages are ready</h1>
  <p style="font-size:16px;line-height:1.5;margin:0 0 20px">${opener} <b>${esc(o.levelName)}</b> (${esc(o.levelTitle)}).
  Your printable PDFs and answer keys are waiting on your download page.</p>
  ${button(o.url, "Download your PDFs")}
  <p style="font-size:15px;line-height:1.5;background:#ffefc2;border-radius:12px;padding:12px 14px;margin:0 0 20px">
  <b>This link works for 7 days, until ${esc(until)}.</b> After that it expires, so download and save your files now.
  Please don't share the link or the files: they're for the children in your home.</p>`);
  return send(mailer, FROM, o.to, subject, text, html, "order");
}

/**
 * To the buyer, once paid: one email with the receipt, the code, where to open it, and the gift card PDF
 * attached to print or send on. Never any download links: the files are for the family who gets the gift.
 * `pdf` is null only if the card couldn't be made; the email then links to the card instead.
 */
export async function sendGiftBuyerEmail(
  mailer: SendEmail | undefined,
  g: {
    to: string;
    code: string;
    what: string; // "every level, ages 3 to 12" or "$50 to spend on any level"
    amount: string;
    childName: string | null;
    cardUrl: string; // the PDF, at /api/gift/:code/card.pdf
    pdf: { filename: string; content: Uint8Array } | null;
  },
): Promise<boolean> {
  if (!mailer) return false;
  const subject = g.childName ? `Your gift card for ${g.childName} is ready` : "Your gift card is ready";
  const thanks = `Thank you! You gave ${g.childName ? `${g.childName} ` : "a gift of "}${g.what} (${g.amount}).`;
  const card = g.pdf
    ? "Your gift card is attached as a PDF. Print it and tuck it into a birthday card, or send it on by email or text."
    : `Download your gift card (PDF) here: ${g.cardUrl}`;
  const text = [
    thanks,
    "",
    card,
    "",
    `Gift code: ${g.code}`,
    "They open it at paperlessons.com/redeem. The code never expires.",
    "",
    "All sales are final: gifts can't be refunded or exchanged for cash. Keep the code safe: anyone who has it can open the gift.",
    "",
    "Paper Lessons · hello@paperlessons.com",
  ].join("\n");
  const html = shell(
    `  <h1 style="font-size:26px;margin:24px 0 8px">${esc(subject)}</h1>
  <p style="font-size:16px;line-height:1.5;margin:0 0 12px">${esc(thanks)}</p>
  <p style="font-size:16px;line-height:1.5;margin:0 0 20px">${g.pdf ? esc(card) : "Your gift card is ready to print or send on."}</p>
  ${g.pdf ? "" : button(g.cardUrl, "Download the gift card (PDF)")}
  <p style="font-size:15px;margin:0 0 4px">Gift code</p>
  <p style="font-family:Menlo,Consolas,monospace;font-size:24px;font-weight:800;letter-spacing:2px;margin:0 0 8px">${esc(g.code)}</p>
  <p style="font-size:16px;line-height:1.5;margin:0 0 20px">They open it at <a href="https://paperlessons.com/redeem" style="color:#e4572e;font-weight:800">paperlessons.com/redeem</a>. The code never expires.</p>
  <p style="font-size:15px;line-height:1.5;background:#ffefc2;border-radius:12px;padding:12px 14px;margin:0 0 20px">
  All sales are final: gifts can't be refunded or exchanged for cash. Keep the code safe: anyone who has it can open the gift.</p>`,
    "Paper Lessons",
  );
  const attachments = g.pdf ? [{ disposition: "attachment" as const, filename: g.pdf.filename, type: "application/pdf", content: g.pdf.content }] : undefined;
  return send(mailer, GIFT_FROM, g.to, subject, text, html, "gift receipt", attachments);
}
